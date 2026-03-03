#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=""
MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTO_MODE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --master) MASTER_DIR="$2"; shift 2 ;;
    --auto) AUTO_MODE=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_DIR" ]]; then
  echo "Usage: sync.sh --project <path> [--master <path>] [--auto]"
  exit 1
fi

CLAUDE_DIR="$PROJECT_DIR/.claude"
LOCK_PATH="$CLAUDE_DIR/workflow.lock"

if [[ ! -f "$LOCK_PATH" ]]; then
  echo "ERROR: No workflow.lock found. Run tools/init.sh first."
  exit 1
fi

# Read lock info
VERSION=$(python3 -c "import json; print(json.load(open('$LOCK_PATH'))['version'])")
STACKS=$(python3 -c "import json; print(','.join(json.load(open('$LOCK_PATH'))['stacks']))")

echo "Syncing project at $PROJECT_DIR (pinned: v$VERSION, stacks: $STACKS)"

# Run drift check in JSON mode
DRIFT_JSON=$("$MASTER_DIR/tools/diff.sh" --project "$PROJECT_DIR" --master "$MASTER_DIR" --json 2>&1) || true

# Parse drift results
BEHIND_FILES=$(echo "$DRIFT_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r['status'] == 'BEHIND':
        print(r['file'])
" 2>/dev/null) || true

DIVERGED_FILES=$(echo "$DRIFT_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r['status'] == 'DIVERGED':
        print(r['file'])
" 2>/dev/null) || true

LOCAL_EDIT_FILES=$(echo "$DRIFT_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r['status'] == 'LOCAL-EDIT':
        print(r['file'])
" 2>/dev/null) || true

MISSING_FILES=$(echo "$DRIFT_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r['status'] == 'MISSING':
        print(r['file'])
" 2>/dev/null) || true

UPDATED=0

# Handle BEHIND files (auto-update)
if [[ -n "$BEHIND_FILES" ]]; then
  echo ""
  echo "BEHIND files (will auto-update):"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    echo "  Updating: $file"
    SOURCE=$(python3 -c "
import os, sys
master='$MASTER_DIR'; rel='$file'; stacks='$STACKS'.split(',')
# Check base
p = os.path.join(master, 'base', rel)
if os.path.exists(p): print(p); sys.exit(0)
# Check stacks
for s in stacks:
    p = os.path.join(master, 'stacks', s, rel)
    if os.path.exists(p): print(p); sys.exit(0)
    if rel.startswith('hooks/'):
        hr = rel[len('hooks/'):]
        p = os.path.join(master, 'stacks', s, 'hooks', hr)
        if os.path.exists(p): print(p); sys.exit(0)
        p = os.path.join(master, 'stacks', s, 'failure-patterns', hr.replace('failure-patterns/', ''))
        if os.path.exists(p): print(p); sys.exit(0)
")
    if [[ -n "$SOURCE" ]]; then
      mkdir -p "$(dirname "$CLAUDE_DIR/$file")"
      cp "$SOURCE" "$CLAUDE_DIR/$file"
      UPDATED=$((UPDATED + 1))
    else
      echo "    WARNING: Could not find master source for $file"
    fi
  done <<< "$BEHIND_FILES"
fi

# Handle MISSING files (restore from master)
if [[ -n "$MISSING_FILES" ]]; then
  echo ""
  echo "MISSING files (will restore):"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    echo "  Restoring: $file"
    SOURCE=$(python3 -c "
import os, sys
master='$MASTER_DIR'; rel='$file'; stacks='$STACKS'.split(',')
p = os.path.join(master, 'base', rel)
if os.path.exists(p): print(p); sys.exit(0)
for s in stacks:
    p = os.path.join(master, 'stacks', s, rel)
    if os.path.exists(p): print(p); sys.exit(0)
    if rel.startswith('hooks/'):
        hr = rel[len('hooks/'):]
        p = os.path.join(master, 'stacks', s, 'hooks', hr)
        if os.path.exists(p): print(p); sys.exit(0)
        p = os.path.join(master, 'stacks', s, 'failure-patterns', hr.replace('failure-patterns/', ''))
        if os.path.exists(p): print(p); sys.exit(0)
")
    if [[ -n "$SOURCE" ]]; then
      mkdir -p "$(dirname "$CLAUDE_DIR/$file")"
      cp "$SOURCE" "$CLAUDE_DIR/$file"
      UPDATED=$((UPDATED + 1))
    fi
  done <<< "$MISSING_FILES"
fi

# Handle DIVERGED files
if [[ -n "$DIVERGED_FILES" ]]; then
  echo ""
  echo "DIVERGED files (both local and master changed):"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ "$AUTO_MODE" == "true" ]]; then
      echo "  SKIP (auto mode): $file — requires manual merge"
    else
      echo "  DIVERGED: $file"
      echo "    Run 'diff $CLAUDE_DIR/$file <master-source>' to compare"
    fi
  done <<< "$DIVERGED_FILES"
fi

# Handle LOCAL-EDIT files
if [[ -n "$LOCAL_EDIT_FILES" ]]; then
  echo ""
  echo "LOCAL-EDIT files (modified locally, master unchanged):"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    echo "  WARNING: $file has local modifications"
  done <<< "$LOCAL_EDIT_FILES"
fi

# Recompose settings.json if any files were updated
if [[ $UPDATED -gt 0 ]]; then
  echo ""
  echo "Recomposing settings.json..."
  python3 "$MASTER_DIR/tools/compose_settings.py" \
    --base "$MASTER_DIR/base/settings.base.json" \
    --guards "$MASTER_DIR/base/guards" \
    --stacks "$STACKS" \
    --stacks-dir "$MASTER_DIR/stacks" \
    --output "$CLAUDE_DIR/settings.json"
fi

# Update workflow.lock
echo "Updating workflow.lock..."
python3 -c "
import json, hashlib, os
from datetime import datetime, timezone

claude_dir = '$CLAUDE_DIR'
lock_path = '$LOCK_PATH'

with open(lock_path) as f:
    lock = json.load(f)

managed = {}
for root, dirs, files in os.walk(claude_dir):
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, claude_dir)
        if rel.startswith(('agent-memory/', 'progress/', 'session-files', 'decisions.log', 'compaction.log')):
            continue
        if rel in ('settings.local.json', 'project-rules.txt'):
            continue
        with open(full, 'rb') as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        managed[rel] = f'sha256:{sha}'

lock['managed'] = managed
lock['lastSync'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

with open(lock_path, 'w') as f:
    json.dump(lock, f, indent=2)
    f.write('\n')
"

echo ""
echo "$UPDATED files updated, 0 files updated" | head -1 | sed "s/0 files updated/$UPDATED files updated/"
if [[ $UPDATED -eq 0 ]] && [[ -z "$DIVERGED_FILES" ]] && [[ -z "$LOCAL_EDIT_FILES" ]]; then
  echo "Project is up to date with master v$VERSION."
fi
