#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_DIR="$(dirname "$SCRIPT_DIR")"

MOCK_PROJECT=$(mktemp -d)
trap "rm -rf $MOCK_PROJECT" EXIT

# Initialize a project first
"$MASTER_DIR/tools/init.sh" --project "$MOCK_PROJECT" --stacks typescript-nestjs --master "$MASTER_DIR"

echo "=== Test 1: No drift on fresh init ==="
OUTPUT=$("$MASTER_DIR/tools/diff.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" 2>&1) && RC=0 || RC=$?
if [[ $RC -ne 0 ]]; then
  echo "FAIL: Fresh init should have zero drift (exit $RC)"
  echo "$OUTPUT"
  exit 1
fi
echo "  PASS: Zero drift on fresh init"

echo "=== Test 2: LOCAL-EDIT detection ==="
# Modify a managed file
echo "# modified" >> "$MOCK_PROJECT/.claude/WORKFLOW.md"
OUTPUT=$("$MASTER_DIR/tools/diff.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" 2>&1) && RC=0 || RC=$?
if [[ $RC -eq 0 ]]; then
  echo "FAIL: Should detect drift after local edit"
  exit 1
fi
if ! echo "$OUTPUT" | grep -q "LOCAL-EDIT"; then
  echo "FAIL: Should report LOCAL-EDIT status"
  echo "$OUTPUT"
  exit 1
fi
echo "  PASS: LOCAL-EDIT detected"

echo "=== Test 3: MISSING detection ==="
# Delete a managed file
rm "$MOCK_PROJECT/.claude/hooks/pre-compact.py"
OUTPUT=$("$MASTER_DIR/tools/diff.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" 2>&1) && RC=0 || RC=$?
if [[ $RC -eq 0 ]]; then
  echo "FAIL: Should detect drift after file deletion"
  exit 1
fi
if ! echo "$OUTPUT" | grep -q "MISSING"; then
  echo "FAIL: Should report MISSING status"
  echo "$OUTPUT"
  exit 1
fi
echo "  PASS: MISSING detected"

echo "=== Test 4: JSON output ==="
OUTPUT=$("$MASTER_DIR/tools/diff.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" --json 2>&1) && RC=0 || RC=$?
if ! echo "$OUTPUT" | python3 -c "import json, sys; d=json.load(sys.stdin); assert 'results' in d" 2>/dev/null; then
  echo "FAIL: JSON output should be valid JSON with results key"
  echo "$OUTPUT"
  exit 1
fi
echo "  PASS: JSON output is valid"

echo ""
echo "ALL TESTS PASSED"
