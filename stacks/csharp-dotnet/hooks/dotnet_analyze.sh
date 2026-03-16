#!/usr/bin/env bash
# PostToolUse hook: Format and analyze C# files after edits.
# Combines dotnet format + Roslyn analysis in a single pass.
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

[ -z "$FILE_PATH" ] && exit 0
[[ "$FILE_PATH" != *.cs ]] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

command -v dotnet >/dev/null 2>&1 || exit 0

# Step 1: Format
dotnet format --include "$FILE_PATH" 2>/dev/null || true

# Step 2: Find nearest .csproj and analyze
DIR=$(dirname "$FILE_PATH")
PROJ=""
while [ "$DIR" != "/" ] && [ "$DIR" != "." ]; do
    FOUND=$(find "$DIR" -maxdepth 1 -name "*.csproj" -print -quit 2>/dev/null || true)
    if [ -n "$FOUND" ]; then
        PROJ="$FOUND"
        break
    fi
    DIR=$(dirname "$DIR")
done

[ -z "$PROJ" ] && exit 0

OUTPUT=$(dotnet build "$PROJ" --no-restore --verbosity quiet 2>&1 || true)

WARNINGS=$(echo "$OUTPUT" | grep -c "warning CS\|warning CA" || true)
ERRORS=$(echo "$OUTPUT" | grep -c "error CS\|error CA" || true)

if [ "$ERRORS" -gt 0 ] || [ "$WARNINGS" -gt 0 ]; then
    echo "{\"systemMessage\": \"[ANALYZE] Roslyn: ${ERRORS} error(s), ${WARNINGS} warning(s) in $(basename "$FILE_PATH"). Review 'dotnet build' output.\"}"
fi

exit 0
