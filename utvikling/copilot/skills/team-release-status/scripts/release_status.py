#!/usr/bin/env python3

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote


DEFAULT_ORG = "navikt"
DEFAULT_TEAM = "teamdokumenthandtering"
DEFAULT_WORKFLOW_PATH = ".github/workflows/deploy-prod.yml"
TRANSIENT_GITHUB_ERRORS = (
	"Bad Gateway",
	"Service Unavailable",
	"Gateway Timeout",
	"HTTP 502",
	"HTTP 503",
	"HTTP 504",
)


class GitHubError(RuntimeError):
	pass


@dataclass(frozen=True)
class Assessment:
	repo: str
	state: str
	reason: str = ""
	ahead_by: int = 0
	release_date: str = ""
	release_age_days: int = 0
	compare_url: str = ""


def gh_json(endpoint: str, *, paginate: bool = False) -> Any:
	command = ["gh", "api"]
	if paginate:
		command.extend(["--paginate", "--slurp"])
	command.append(endpoint)
	for attempt in range(4):
		result = subprocess.run(command, capture_output=True, text=True, check=False)
		if result.returncode == 0:
			break
		message = result.stderr.strip() or result.stdout.strip() or "unknown GitHub CLI error"
		if attempt == 3 or not any(error in message for error in TRANSIENT_GITHUB_ERRORS):
			raise GitHubError(message)
		time.sleep(0.5 * (2**attempt))
	try:
		return json.loads(result.stdout)
	except json.JSONDecodeError as error:
		raise GitHubError(f"invalid JSON from gh for {endpoint}: {error}") from error


def latest_release_run(org: str, repo: str, workflow_id: int) -> dict[str, Any] | None:
	releases = gh_json(f"repos/{org}/{repo}/releases?per_page=100")
	published_releases = sorted(
		(
			release
			for release in releases
			if not release.get("draft") and release.get("published_at")
		),
		key=lambda release: release["published_at"],
		reverse=True,
	)
	if not published_releases:
		return None

	for release in published_releases:
		tag = str(release["tag_name"])
		for attempt in range(3):
			tag_runs_payload = gh_json(
				f"repos/{org}/{repo}/actions/workflows/{workflow_id}/runs"
				f"?event=release&branch={quote(tag, safe='')}&per_page=10"
			)
			runs = tag_runs_payload.get("workflow_runs", [])
			if runs or attempt == 2:
				break
			time.sleep(0.25 * (attempt + 1))

		tag_runs = [
			run
			for run in runs
			if run.get("head_branch") == tag
			and run.get("event") == "release"
			and run.get("conclusion") == "success"
		]
		if tag_runs:
			return max(tag_runs, key=lambda run: run["created_at"])
	return None


def paginated_items(payload: Any) -> list[dict[str, Any]]:
	if not isinstance(payload, list):
		raise GitHubError("unexpected paginated response")
	items: list[dict[str, Any]] = []
	for page in payload:
		if not isinstance(page, list):
			raise GitHubError("unexpected page in paginated response")
		items.extend(page)
	return items


def release_age_days(created_at: str, now: dt.datetime) -> int:
	released = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
	if released.tzinfo is None:
		released = released.replace(tzinfo=dt.UTC)
	return max(0, int((now - released.astimezone(dt.UTC)).total_seconds() // 86_400))


def assess_repo(
	org: str,
	repo: dict[str, Any],
	workflow_path: str,
	now: dt.datetime,
) -> Assessment:
	name = str(repo["name"])
	if repo.get("archived"):
		return Assessment(name, "excluded", "arkivert")

	try:
		workflows_payload = gh_json(f"repos/{org}/{name}/actions/workflows?per_page=100")
		workflows = workflows_payload.get("workflows", [])
		workflow = next(
			(
				item
				for item in workflows
				if item.get("path") == workflow_path and item.get("state") == "active"
			),
			None,
		)
		if workflow is None:
			return Assessment(name, "excluded", f"mangler aktiv {workflow_path}")

		run = latest_release_run(org, name, int(workflow["id"]))
		if run is None:
			return Assessment(name, "excluded", "ingen vellykket produksjonsrelease")

		release_sha = run["head_sha"]
		default_branch = repo.get("default_branch")
		if not default_branch:
			return Assessment(name, "error", "repoet mangler default branch")

		head = gh_json(f"repos/{org}/{name}/commits/{quote(str(default_branch), safe='')}")
		head_sha = head["sha"]
		comparison = gh_json(f"repos/{org}/{name}/compare/{release_sha}...{head_sha}")
		status = comparison.get("status")
		if status == "diverged":
			return Assessment(name, "error", "prod-commit og default branch har divergerte historikker")

		ahead_by = int(comparison.get("ahead_by", 0))
		created_at = run["created_at"]
		release_date = created_at[:10]
		compare_url = f"https://github.com/{org}/{name}/compare/{release_sha}...{head_sha}"
		return Assessment(
			name,
			"unreleased" if ahead_by > 0 else "released",
			ahead_by=ahead_by,
			release_date=release_date,
			release_age_days=release_age_days(created_at, now),
			compare_url=compare_url,
		)
	except (GitHubError, KeyError, TypeError, ValueError) as error:
		return Assessment(name, "error", str(error).replace("\n", " "))


def parse_now(value: str | None) -> dt.datetime:
	if value is None:
		return dt.datetime.now(dt.UTC)
	parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
	if parsed.tzinfo is None:
		parsed = parsed.replace(tzinfo=dt.UTC)
	return parsed.astimezone(dt.UTC)


def print_report(
	org: str,
	team: str,
	assessments: list[Assessment],
	show_excluded: bool,
) -> None:
	unreleased = sorted(
		(item for item in assessments if item.state == "unreleased"),
		key=lambda item: (-item.ahead_by, item.repo.lower()),
	)
	released_count = sum(item.state == "released" for item in assessments)
	excluded = sorted(
		(item for item in assessments if item.state == "excluded"),
		key=lambda item: item.repo.lower(),
	)
	errors = sorted(
		(item for item in assessments if item.state == "error"),
		key=lambda item: item.repo.lower(),
	)
	deployable_count = len(unreleased) + released_count

	print(
		f"**{len(unreleased)} av {deployable_count} deploybare repoer i "
		f"`{org}/{team}` har commits som ikke er releaset til prod.**"
	)
	print()
	print("| Repo | Commits foran prod | Siste release | Dager siden release | Endringer |")
	print("|---|---:|---:|---:|---|")
	for item in unreleased:
		print(
			f"| [{item.repo}](https://github.com/{org}/{item.repo}) "
			f"| {item.ahead_by} | {item.release_date} | {item.release_age_days} "
			f"| [Sammenlign]({item.compare_url}) |"
		)
	if not unreleased:
		print("| _Ingen_ | 0 | – | – | – |")

	if show_excluded and excluded:
		print()
		print("**Ikke vurdert som deploybare**")
		print()
		print("| Repo | Årsak |")
		print("|---|---|")
		for item in excluded:
			print(f"| {item.repo} | {item.reason} |")

	if errors:
		print()
		print("**Kunne ikke vurderes**")
		print()
		print("| Repo | Feil |")
		print("|---|---|")
		for item in errors:
			print(f"| {item.repo} | {item.reason} |")


def write_html_report(
	org: str,
	team: str,
	assessments: list[Assessment],
	generated_at: dt.datetime,
	output: Path,
) -> Path:
	output = output.expanduser().resolve()
	output.parent.mkdir(parents=True, exist_ok=True)
	data = [
		{
			"repo": item.repo,
			"state": item.state,
			"reason": item.reason,
			"aheadBy": item.ahead_by,
			"releaseDate": item.release_date,
			"releaseAgeDays": item.release_age_days,
			"repoUrl": f"https://github.com/{org}/{item.repo}",
			"releasesUrl": f"https://github.com/{org}/{item.repo}/releases",
			"compareUrl": item.compare_url,
		}
		for item in assessments
	]
	safe_data = (
		json.dumps(data, ensure_ascii=False)
		.replace("&", "\\u0026")
		.replace("<", "\\u003c")
		.replace(">", "\\u003e")
	)
	title = html.escape(f"Release-status · {org}/{team}")
	generated = generated_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")
	document = f"""<!doctype html>
<html lang="nb">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>{title}</title>
	<style>
		:root {{
			color-scheme: light dark;
			--bg: #f4f5f7;
			--panel: #fff;
			--text: #23262a;
			--muted: #5f6670;
			--border: #d8dde5;
			--accent: #0067c5;
			--warning: #b45309;
			--danger: #b42318;
			--success: #087f5b;
			font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
		}}
		@media (prefers-color-scheme: dark) {{
			:root {{
				--bg: #15171a;
				--panel: #202328;
				--text: #f2f4f7;
				--muted: #aab1bb;
				--border: #3a4049;
				--accent: #66b3ff;
				--warning: #fbbf24;
				--danger: #ff8a80;
				--success: #5ee0b1;
			}}
		}}
		* {{ box-sizing: border-box; }}
		body {{ margin: 0; background: var(--bg); color: var(--text); }}
		main {{ width: min(1180px, calc(100% - 32px)); margin: 40px auto 72px; }}
		h1 {{ margin: 0 0 6px; font-size: clamp(1.7rem, 4vw, 2.5rem); }}
		.subtitle {{ color: var(--muted); margin: 0 0 28px; }}
		.cards {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; margin-bottom: 22px; }}
		.card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }}
		.card strong {{ display: block; font-size: 1.8rem; }}
		.card span {{ color: var(--muted); font-size: .9rem; }}
		.controls {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }}
		input, select {{
			background: var(--panel); color: var(--text); border: 1px solid var(--border);
			border-radius: 8px; padding: 10px 12px; font: inherit;
		}}
		input {{ flex: 1 1 260px; }}
		select {{ min-width: 210px; }}
		.table-wrap {{ overflow-x: auto; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }}
		table {{ width: 100%; border-collapse: collapse; }}
		th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }}
		th {{ font-size: .82rem; color: var(--muted); text-transform: uppercase; letter-spacing: .035em; }}
		th[data-sort] {{ cursor: pointer; user-select: none; }}
		th[data-sort]:hover {{ color: var(--accent); }}
		tbody tr:last-child td {{ border-bottom: 0; }}
		tbody tr:hover {{ background: color-mix(in srgb, var(--accent) 7%, transparent); }}
		td.numeric, th.numeric {{ text-align: right; }}
		a {{ color: var(--accent); text-decoration: none; }}
		a:hover {{ text-decoration: underline; }}
		.badge {{ display: inline-block; border-radius: 999px; padding: 3px 9px; font-size: .78rem; font-weight: 650; }}
		.unreleased {{ color: var(--warning); background: color-mix(in srgb, var(--warning) 14%, transparent); }}
		.released {{ color: var(--success); background: color-mix(in srgb, var(--success) 14%, transparent); }}
		.excluded {{ color: var(--muted); background: color-mix(in srgb, var(--muted) 14%, transparent); }}
		.error {{ color: var(--danger); background: color-mix(in srgb, var(--danger) 14%, transparent); }}
		.empty {{ padding: 32px; color: var(--muted); text-align: center; }}
		.note {{ color: var(--muted); font-size: .88rem; margin-top: 14px; }}
		@media (max-width: 700px) {{
			main {{ width: min(100% - 20px, 1180px); margin-top: 20px; }}
			.cards {{ grid-template-columns: repeat(2, 1fr); }}
		}}
	</style>
</head>
<body>
	<main>
		<h1>Release-status</h1>
		<p class="subtitle">{html.escape(org)}/{html.escape(team)} · generert {html.escape(generated)}</p>
		<section class="cards" aria-label="Oppsummering">
			<div class="card"><strong id="unreleased-count">0</strong><span>venter på release</span></div>
			<div class="card"><strong id="deployable-count">0</strong><span>deploybare repoer</span></div>
			<div class="card"><strong id="excluded-count">0</strong><span>ikke deploybare</span></div>
			<div class="card"><strong id="error-count">0</strong><span>feil</span></div>
		</section>
		<section class="controls" aria-label="Filtrering">
			<input id="search" type="search" placeholder="Søk etter repo eller årsak…" autocomplete="off">
			<select id="state-filter">
				<option value="unreleased">Venter på release</option>
				<option value="deployable">Alle deploybare</option>
				<option value="all">Alle repoer</option>
				<option value="released">Oppdatert i prod</option>
				<option value="excluded">Ikke deploybare</option>
				<option value="error">Kunne ikke vurderes</option>
			</select>
		</section>
		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						<th data-sort="repo">Repo</th>
						<th data-sort="state">Status</th>
						<th class="numeric" data-sort="aheadBy">Commits foran prod</th>
						<th data-sort="releaseDate">Siste release</th>
						<th class="numeric" data-sort="releaseAgeDays">Dager siden release</th>
						<th>Releases</th>
						<th>Detaljer</th>
					</tr>
				</thead>
				<tbody id="rows"></tbody>
			</table>
			<div id="empty" class="empty" hidden>Ingen repoer matcher filteret.</div>
		</div>
		<p class="note">«Commits foran prod» inkluderer alle commits på default branch og tilsvarer ikke nødvendigvis antall PR-er.</p>
	</main>
	<script>
		const reports = {safe_data};
		const labels = {{
			unreleased: "Venter på release",
			released: "Oppdatert i prod",
			excluded: "Ikke deploybar",
			error: "Feil"
		}};
		const rows = document.querySelector("#rows");
		const empty = document.querySelector("#empty");
		const search = document.querySelector("#search");
		const stateFilter = document.querySelector("#state-filter");
		let sortKey = "aheadBy";
		let sortDirection = -1;

		const count = state => reports.filter(item => item.state === state).length;
		document.querySelector("#unreleased-count").textContent = count("unreleased");
		document.querySelector("#deployable-count").textContent = count("unreleased") + count("released");
		document.querySelector("#excluded-count").textContent = count("excluded");
		document.querySelector("#error-count").textContent = count("error");

		function matchesState(item) {{
			const selected = stateFilter.value;
			if (selected === "all") return true;
			if (selected === "deployable") return item.state === "unreleased" || item.state === "released";
			return item.state === selected;
		}}

		function compare(left, right) {{
			const a = left[sortKey] ?? "";
			const b = right[sortKey] ?? "";
			if (typeof a === "number" && typeof b === "number") return (a - b) * sortDirection;
			return String(a).localeCompare(String(b), "nb", {{ numeric: true }}) * sortDirection;
		}}

		function cell(text, className = "") {{
			const element = document.createElement("td");
			element.textContent = text;
			if (className) element.className = className;
			return element;
		}}

		function render() {{
			const query = search.value.trim().toLocaleLowerCase("nb");
			const visible = reports
				.filter(item => matchesState(item))
				.filter(item => `${{item.repo}} ${{item.reason}}`.toLocaleLowerCase("nb").includes(query))
				.sort(compare);
			rows.replaceChildren();
			for (const item of visible) {{
				const row = document.createElement("tr");
				const repoCell = document.createElement("td");
				const repoLink = document.createElement("a");
				repoLink.href = item.repoUrl;
				repoLink.target = "_blank";
				repoLink.rel = "noreferrer";
				repoLink.textContent = item.repo;
				repoCell.append(repoLink);
				row.append(repoCell);

				const statusCell = document.createElement("td");
				const badge = document.createElement("span");
				badge.className = `badge ${{item.state}}`;
				badge.textContent = labels[item.state];
				statusCell.append(badge);
				row.append(statusCell);
				row.append(cell(item.state === "unreleased" ? item.aheadBy : "–", "numeric"));
				row.append(cell(item.releaseDate || "–"));
				row.append(cell(item.releaseDate ? item.releaseAgeDays : "–", "numeric"));

				const releasesCell = document.createElement("td");
				const releasesLink = document.createElement("a");
				releasesLink.href = item.releasesUrl;
				releasesLink.target = "_blank";
				releasesLink.rel = "noreferrer";
				releasesLink.textContent = "Releases";
				releasesCell.append(releasesLink);
				row.append(releasesCell);

				const detailsCell = document.createElement("td");
				if (item.compareUrl) {{
					const compareLink = document.createElement("a");
					compareLink.href = item.compareUrl;
					compareLink.target = "_blank";
					compareLink.rel = "noreferrer";
					compareLink.textContent = "Sammenlign";
					detailsCell.append(compareLink);
				}} else {{
					detailsCell.textContent = item.reason || "–";
				}}
				row.append(detailsCell);
				rows.append(row);
			}}
			empty.hidden = visible.length > 0;
		}}

		for (const heading of document.querySelectorAll("th[data-sort]")) {{
			heading.addEventListener("click", () => {{
				const nextKey = heading.dataset.sort;
				if (sortKey === nextKey) sortDirection *= -1;
				else {{
					sortKey = nextKey;
					sortDirection = nextKey === "repo" || nextKey === "state" || nextKey === "releaseDate" ? 1 : -1;
				}}
				render();
			}});
		}}
		search.addEventListener("input", render);
		stateFilter.addEventListener("change", render);
		render();
	</script>
</body>
</html>
"""
	output.write_text(document, encoding="utf-8")
	return output


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Finn team-repoer med commits som ikke er releaset til produksjon."
	)
	parser.add_argument("--org", default=DEFAULT_ORG)
	parser.add_argument("--team", default=DEFAULT_TEAM)
	parser.add_argument("--workflow-path", default=DEFAULT_WORKFLOW_PATH)
	parser.add_argument("--show-excluded", action="store_true")
	parser.add_argument(
		"--markdown",
		action="store_true",
		help="Skriv Markdown til terminalen i stedet for å lage en nettside.",
	)
	parser.add_argument(
		"--output",
		type=Path,
		help="Filsti for HTML-rapporten.",
	)
	parser.add_argument(
		"--as-of",
		help=argparse.SUPPRESS,
	)
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	try:
		repositories = paginated_items(
			gh_json(
				f"orgs/{args.org}/teams/{args.team}/repos?per_page=100",
				paginate=True,
			)
		)
	except GitHubError as error:
		print(f"Kunne ikke hente repoer for {args.org}/{args.team}: {error}", file=sys.stderr)
		return 1

	now = parse_now(args.as_of)
	with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
		assessments = list(
			executor.map(
				lambda repo: assess_repo(args.org, repo, args.workflow_path, now),
				repositories,
			)
		)

	has_errors = any(item.state == "error" for item in assessments)
	if args.markdown:
		print_report(args.org, args.team, assessments, args.show_excluded)
	else:
		default_output = (
			Path.home()
			/ ".copilot"
			/ "reports"
			/ f"{args.org}-{args.team}-release-status.html"
		)
		report_path = write_html_report(
			args.org,
			args.team,
			assessments,
			now,
			args.output or default_output,
		)
		print(f"Rapport skrevet til {report_path}")
	return 2 if has_errors else 0


if __name__ == "__main__":
	raise SystemExit(main())
