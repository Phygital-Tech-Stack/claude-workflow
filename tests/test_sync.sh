#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_DIR="$(dirname "$SCRIPT_DIR")"

MOCK_PROJECT=$(mktemp -d)
trap "rm -rf $MOCK_PROJECT" EXIT

# Initialize a project
"$MASTER_DIR/tools/init.sh" --project "$MOCK_PROJECT" --stacks typescript-nestjs --master "$MASTER_DIR"

echo "=== Test 1: Sync on fresh init (no changes needed) ==="
OUTPUT=$("$MASTER_DIR/tools/sync.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" --auto 2>&1) && RC=0 || RC=$?
if [[ $RC -ne 0 ]]; then
  echo "FAIL: Sync on fresh init should succeed (exit $RC)"
  echo "$OUTPUT"
  exit 1
fi
if ! echo "$OUTPUT" | grep -qi "up to date\|no changes\|0 files updated"; then
  echo "WARN: Expected 'up to date' message but sync succeeded"
fi
echo "  PASS: Sync on fresh init succeeds"

echo "=== Test 2: Sync updates BEHIND files ==="
# Simulate master having a newer version of a file:
# Modify the master source directly (simulating a new master release)
ORIG_WORKFLOW=$(cat "$MASTER_DIR/base/WORKFLOW.md")
echo "# Updated by test" >> "$MASTER_DIR/base/WORKFLOW.md"

# Now the project's WORKFLOW.md is BEHIND master
OUTPUT=$("$MASTER_DIR/tools/sync.sh" --project "$MOCK_PROJECT" --master "$MASTER_DIR" --auto 2>&1) && RC=0 || RC=$?
# Restore master
echo "$ORIG_WORKFLOW" > "$MASTER_DIR/base/WORKFLOW.md"

if ! echo "$OUTPUT" | grep -q "BEHIND\|updated"; then
  echo "FAIL: Should detect BEHIND files and update them"
  echo "$OUTPUT"
  exit 1
fi
echo "  PASS: BEHIND files detected and synced"

echo "=== Test 3: Lock file is updated after sync ==="
if [[ ! -f "$MOCK_PROJECT/.claude/workflow.lock" ]]; then
  echo "FAIL: workflow.lock should exist after sync"
  exit 1
fi
# Verify lock has managed entries
if ! python3 -c "import json; l=json.load(open('$MOCK_PROJECT/.claude/workflow.lock')); assert len(l['managed']) > 0" 2>/dev/null; then
  echo "FAIL: workflow.lock should have managed entries"
  exit 1
fi
echo "  PASS: Lock file updated"

echo ""
echo "ALL TESTS PASSED"
