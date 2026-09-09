---
name: team-release-status
description: Finn NAV-repoer som tilhører et GitHub-team og har commits på default branch som ikke er releaset til produksjon, og presenter resultatet som en lokal interaktiv webside. Bruk denne skillen når brukeren spør hvilke av teamets repoer som venter på release, ligger foran prod, har endringer på main/master som ikke er deployet, ønsker en release-statusside eller vil se hvor gammel siste produksjonsrelease er.
compatibility: Krever GitHub CLI (`gh`), Python 3.11 eller nyere og en autentisert GitHub-bruker med lesetilgang til organisasjonens team, repoer, releases og Actions-kjøringer.
---

# Team release status

Bruk det medfølgende scriptet for å lage rapporten. Ikke utled teamets repoer fra lokalt klonede repoer; GitHub-teamets repository-tilknytninger er den autoritative kilden.

## Standardkjøring

Kjør fra skillens katalog med `python3`. Standardkjøringen lager en selvstendig
HTML-fil i `~/.copilot/reports/`:

```bash
python3 scripts/release_status.py
```

Standardverdiene er:

- organisasjon: `navikt`
- team-slug: `teamdokumenthandtering`
- produksjonsworkflow: `.github/workflows/deploy-prod.yml`

Disse standardene er tilpasset Team Dokumenthåndtering. Overstyr dem for andre
GitHub-team:

```bash
python3 scripts/release_status.py --org navikt --team <team-slug>
```

Bruk `--output <fil.html>` for å velge filsti. Bruk `--markdown` for den gamle
terminalrapporten; `--show-excluded` gjelder bare i Markdown-modus.

## Definisjoner

Et repo tilhører teamet når GitHub API-et returnerer det fra
`orgs/{org}/teams/{team}/repos`.

Et repo regnes som deploybart når det:

1. ikke er arkivert
2. har en aktiv workflow med eksakt path `.github/workflows/deploy-prod.yml`
3. har minst én vellykket workflow-kjøring trigget av en publisert GitHub Release

Siste vellykkede release-run representerer produksjonsversjonen. Bruk GitHub
Releases som fasit for siste publiserte release og slå opp prod-workflowen direkte
med hver release-tag i datoorden. Gjenta tag-oppslaget ved tom respons og ikke
fall tilbake til en bred liste over workflow-runs; slike lister har vist seg å
kunne mangle nyere kjøringer. Hvis siste release ikke ble deployet, bruk første
eldre publiserte release med vellykket prod-workflow. Repoets default branch
representerer kandidatversjonen. GitHub Compare API avgjør hvor mange commits
branchen ligger foran produksjonsversjonen.

Gjenta midlertidige GitHub-feil som 502, 503 og 504 med backoff. Rapporter andre
API-feil eksplisitt; de må ikke omgjøres til eldre release-data.

«Dager siden release» er antall hele døgn fra tidspunktet da siste vellykkede prod-workflow ble opprettet, målt i UTC.

Dependabot-pause hentes fra `repos/{org}/{repo}/automated-security-fixes`.
Feltet `paused` avgjør om oppdateringer er pauset. Feltet `enabled` gjelder
Dependabot security updates og må ikke brukes til å avgjøre om vanlige
versjonsoppdateringer fra `dependabot.yml` er aktive. HTTP 404 vises som ukjent.
Andre feil ved oppslag skal vises eksplisitt og gjøre rapporten ufullstendig.

## Nettsiden

Nettsiden viser alle teamets repoer og åpner med filteret «Venter på release».
Den inneholder:

- oppsummeringskort for release-etterslep, deploybare repoer, utelatelser og feil
- fritekstsøk etter repo eller utelatelsesårsak
- statusfilter for unreleased, deploybare, oppdaterte, utelatte og feilende repoer
- statusfilter for repoer der Dependabot er pauset
- sorterbare kolonner
- lenker til repo og GitHub Compare
- egen Releases-lenke til `https://github.com/{org}/{repo}/releases`
- antall åpne pull requests med lenke til repoets pull requests
- dato og alder i hele dager for siste produksjonsrelease

Etter vellykket kjøring, returner den komplette absolutte filstien scriptet skrev
ut, slik at brukeren kan kopiere den inn i nettleseren. Ikke forsøk å åpne
nettleseren, og ikke gjengi hele tabellen i terminalen.

Ikke skjul manglende tilgang, API-feil eller divergerte branches. Nettsiden viser
slike repoer med status «Feil». Si at resultatet er ufullstendig dersom scriptet
avslutter med status 2.
