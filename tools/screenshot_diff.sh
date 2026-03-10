#!/usr/bin/env bash
set -euo pipefail

# Compare two screenshots using ImageMagick.
# Usage: screenshot_diff.sh <baseline> <current> [diff-output]
# Exit 0 if identical, 1 if different.

if [[ $# -lt 2 ]]; then
  echo "Usage: screenshot_diff.sh <baseline> <current> [diff-output]"
  echo "  Compares two images using ImageMagick compare."
  echo "  Exit 0 = identical, Exit 1 = different."
  exit 2
fi

BASELINE="$1"
CURRENT="$2"
DIFF_OUT="${3:-/tmp/screenshot-diff.png}"

if ! command -v compare &>/dev/null; then
  echo "ERROR: ImageMagick 'compare' not found. Install with: apt install imagemagick" >&2
  exit 2
fi

METRIC=$(compare -metric AE "$BASELINE" "$CURRENT" "$DIFF_OUT" 2>&1) || true

if [[ "$METRIC" == "0" ]]; then
  echo "PASS: Images are identical"
  exit 0
else
  echo "DIFF: $METRIC pixels differ (see $DIFF_OUT)"
  exit 1
fi
