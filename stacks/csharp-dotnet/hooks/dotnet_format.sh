#!/usr/bin/env bash
# PostToolUse hook: auto-format C# files with dotnet format after edits.
set -euo pipefail

FILE="${TOOL_INPUT_FILE_PATH:-}"
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.cs ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

if command -v dotnet &>/dev/null; then
  dotnet format --include "$FILE" 2>/dev/null || true
fi
