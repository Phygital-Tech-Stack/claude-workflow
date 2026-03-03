#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=""
MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_FORMAT="text"  # text or json

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --master) MASTER_DIR="$2"; shift 2 ;;
    --json) OUTPUT_FORMAT="json"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_DIR" ]]; then
  echo "Usage: diff.sh --project <path> [--master <path>] [--json]"
  exit 1
fi

python3 "$MASTER_DIR/tools/drift_check.py" \
  --project "$PROJECT_DIR" \
  --master "$MASTER_DIR" \
  --format "$OUTPUT_FORMAT"
