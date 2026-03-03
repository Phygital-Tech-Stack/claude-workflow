#!/usr/bin/env bash
# PostToolUse hook: run mypy type check on edited Python files.
set -euo pipefail

FILE="${TOOL_INPUT_FILE_PATH:-}"
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

if command -v mypy &>/dev/null; then
  OUTPUT=$(mypy "$FILE" --no-error-summary 2>&1) || true
  if echo "$OUTPUT" | grep -q "error:"; then
    echo "mypy found type errors in $FILE:"
    echo "$OUTPUT" | grep "error:" | head -5
  fi
fi
