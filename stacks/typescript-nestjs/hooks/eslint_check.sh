#!/usr/bin/env bash
# PostToolUse hook: Run ESLint on TypeScript files after edits.
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

[ -z "$FILE_PATH" ] && exit 0
[[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.tsx ]] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Skip if eslint not available
command -v npx >/dev/null 2>&1 || exit 0
[ ! -f "node_modules/.bin/eslint" ] && exit 0

OUTPUT=$(npx eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>/dev/null || true)

if [ -n "$OUTPUT" ] && echo "$OUTPUT" | grep -q "Error\|Warning"; then
    # Count issues
    ERRORS=$(echo "$OUTPUT" | grep -c "Error" || true)
    WARNINGS=$(echo "$OUTPUT" | grep -c "Warning" || true)
    echo "{\"systemMessage\": \"[LINT] ESLint: ${ERRORS} error(s), ${WARNINGS} warning(s) in $(basename "$FILE_PATH"). Run 'npx eslint --fix' to auto-fix.\"}"
fi

exit 0
