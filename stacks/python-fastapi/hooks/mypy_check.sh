#!/usr/bin/env bash
# PostToolUse hook: run mypy type check on edited Python files.
set -euo pipefail

FILE="${TOOL_INPUT_FILE_PATH:-}"
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
VENV_MYPY="$REPO_ROOT/.venv/bin/mypy"
MYPY="${VENV_MYPY}"
[[ ! -x "$MYPY" ]] && MYPY="$(command -v mypy 2>/dev/null || true)"
[[ -z "$MYPY" ]] && exit 0

OUTPUT=$("$MYPY" "$FILE" --no-error-summary 2>&1) || true
if echo "$OUTPUT" | grep -q "error:"; then
  echo "mypy found type errors in $FILE:"
  echo "$OUTPUT" | grep "error:" | head -5
fi
