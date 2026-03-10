#!/usr/bin/env bash
# PostToolUse hook: Auto-format TypeScript files with Prettier after edits.
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

[ -z "$FILE_PATH" ] && exit 0
[[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.tsx ]] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Skip if prettier not available
command -v npx >/dev/null 2>&1 || exit 0
[ ! -f "node_modules/.bin/prettier" ] && exit 0

npx prettier --write "$FILE_PATH" --log-level silent 2>/dev/null || true
exit 0
