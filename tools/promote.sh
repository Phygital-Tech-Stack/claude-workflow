#!/usr/bin/env bash
set -euo pipefail

FILE_PATH=""
PROJECT_DIR=""
TARGET=""  # base or stack name

while [[ $# -gt 0 ]]; do
  case $1 in
    --file) FILE_PATH="$2"; shift 2 ;;
    --from) PROJECT_DIR="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

if [[ -z "$FILE_PATH" || -z "$PROJECT_DIR" ]]; then
  echo "Usage: promote.sh --file <path-in-.claude/> --from <project-dir> [--target base|<stack>]"
  exit 1
fi

TARGET=${TARGET:-base}
SOURCE="$PROJECT_DIR/.claude/$FILE_PATH"

if [[ ! -f "$SOURCE" ]]; then
  echo "ERROR: $SOURCE not found"
  exit 1
fi

# Determine destination
MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$MASTER_DIR/$TARGET/$FILE_PATH"

echo "Promoting: $SOURCE"
echo "      To: $DEST"
echo "  Target: $TARGET"

mkdir -p "$(dirname "$DEST")"
cp "$SOURCE" "$DEST"

echo ""
echo "File copied. Next steps:"
echo "  1. Review $DEST for project-specific references"
echo "  2. Strip any hardcoded paths or domain terms"
echo "  3. git add && git commit"
echo "  4. Push and open PR on claude-workflow"
