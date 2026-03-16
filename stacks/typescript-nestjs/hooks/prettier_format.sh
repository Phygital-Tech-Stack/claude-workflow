#!/usr/bin/env bash
# PostToolUse hook: Format with Prettier then lint with ESLint on TypeScript files.
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

[ -z "$FILE_PATH" ] && exit 0
[[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.tsx ]] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

command -v npx >/dev/null 2>&1 || exit 0

# Step 1: Prettier format
if [ -f "node_modules/.bin/prettier" ]; then
    npx prettier --write "$FILE_PATH" --log-level silent 2>/dev/null || true
fi

# Step 2: ESLint check
if [ -f "node_modules/.bin/eslint" ]; then
    OUTPUT=$(npx eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>/dev/null || true)
    if [ -n "$OUTPUT" ] && echo "$OUTPUT" | grep -q "Error\|Warning"; then
        ERRORS=$(echo "$OUTPUT" | grep -c "Error" || true)
        WARNINGS=$(echo "$OUTPUT" | grep -c "Warning" || true)
        echo "{\"systemMessage\": \"[LINT] ESLint: ${ERRORS} error(s), ${WARNINGS} warning(s) in $(basename "$FILE_PATH"). Run 'npx eslint --fix' to auto-fix.\"}"
    fi
fi

exit 0
