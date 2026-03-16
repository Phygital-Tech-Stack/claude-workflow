#!/usr/bin/env bash
# PostToolUse hook: auto-format Python files with ruff after edits.
set -euo pipefail

FILE="${TOOL_INPUT_FILE_PATH:-}"
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
VENV_RUFF="$REPO_ROOT/.venv/bin/ruff"
RUFF="${VENV_RUFF}"
[[ ! -x "$RUFF" ]] && RUFF="$(command -v ruff 2>/dev/null || true)"
[[ -z "$RUFF" ]] && exit 0

"$RUFF" format "$FILE" 2>/dev/null || true
"$RUFF" check --fix "$FILE" 2>/dev/null || true
