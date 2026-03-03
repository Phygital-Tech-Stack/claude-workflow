#!/usr/bin/env bash
# PostToolUse hook: auto-format Python files with ruff after edits.
set -euo pipefail

FILE="${TOOL_INPUT_FILE_PATH:-}"
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

if command -v ruff &>/dev/null; then
  ruff format "$FILE" 2>/dev/null || true
  ruff check --fix "$FILE" 2>/dev/null || true
fi
