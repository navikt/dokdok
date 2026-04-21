#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Output helpers ---
info()  { printf '\033[0;34m%s\033[0m\n' "$*"; }
ok()    { printf '\033[0;32m✓ %s\033[0m\n' "$*"; }
warn()  { printf '\033[0;33m⚠ %s\033[0m\n' "$*"; }
skip()  { printf '\033[0;90m· %s (already linked)\033[0m\n' "$*"; }
err()   { printf '\033[0;31m✗ %s\033[0m\n' "$*" >&2; }

# --- Idempotent symlink ---
# link_safe <target> <source>
link_safe() {
  local target="$1"
  local source="$2"

  if [[ -L "$target" ]]; then
    local existing
    existing="$(readlink "$target")"
    if [[ "$existing" == "$source" ]]; then
      skip "$target"
      return
    else
      warn "$target points to '$existing', relinking to '$source'"
      ln -sfn "$source" "$target"
      ok "$target"
    fi
  elif [[ -e "$target" ]]; then
    err "$target exists and is not a symlink — skipping to avoid data loss"
  else
    mkdir -p "$(dirname "$target")"
    ln -s "$source" "$target"
    ok "$target"
  fi
}

# --- Setup functions ---
setup_personal() {
  info "Setting up ~/.copilot/ ..."
  mkdir -p ~/.copilot
  link_safe ~/.copilot/copilot-instructions.md "$SCRIPT_DIR/instructions/copilot-instructions.md"
  link_safe ~/.copilot/skills                  "$SCRIPT_DIR/skills"
  link_safe ~/.copilot/agents                  "$SCRIPT_DIR/agents"
}

setup_repo() {
  local repo="$1"
  if [[ ! -d "$repo" ]]; then
    err "Repo path '$repo' does not exist"
    exit 1
  fi
  info "Setting up $repo/.github/instructions ..."
  mkdir -p "$repo/.github"
  link_safe "$repo/.github/instructions" "$SCRIPT_DIR/instructions/scoped"
}

setup_opencode() {
  info "Setting up ~/.config/opencode/ ..."
  mkdir -p ~/.config/opencode
  link_safe ~/.config/opencode/skills    "$SCRIPT_DIR/skills"
  link_safe ~/.config/opencode/AGENTS.md "$SCRIPT_DIR/instructions/copilot-instructions.md"
}

# --- Usage ---
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Sets up symlinks for Copilot instructions, skills, and agents.

Options:
  --personal        Set up ~/.copilot/ (instructions, skills, agents)
  --repo <path>     Set up .github/instructions in an app repo
  --opencode        Set up ~/.config/opencode/ (skills, AGENTS.md)
  --all             Shorthand for --personal --opencode
  -h, --help        Show this help

Examples:
  $(basename "$0") --personal
  $(basename "$0") --all
  $(basename "$0") --repo ~/nav/min-app
  $(basename "$0") --personal --repo ~/nav/min-app
EOF
}

# --- Parse args ---
if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

DO_PERSONAL=false
DO_OPENCODE=false
REPO_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --personal)  DO_PERSONAL=true ;;
    --opencode)  DO_OPENCODE=true ;;
    --all)       DO_PERSONAL=true; DO_OPENCODE=true ;;
    --repo)
      shift
      if [[ -z "${1:-}" ]]; then
        err "--repo requires a path argument"
        exit 1
      fi
      REPO_PATH="$1"
      ;;
    -h|--help)   usage; exit 0 ;;
    *)
      err "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

# --- Dispatch ---
$DO_PERSONAL && setup_personal
$DO_OPENCODE && setup_opencode
[[ -n "$REPO_PATH" ]] && setup_repo "$REPO_PATH"

echo ""
ok "Done."
