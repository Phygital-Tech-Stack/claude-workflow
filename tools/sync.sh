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

# Resolve {{PLACEHOLDER}} values in updated .md files
if [[ $UPDATED -gt 0 ]]; then
  echo ""
  echo "Resolving placeholders..."
  python3 -c "
import os, yaml

claude_dir = '$CLAUDE_DIR'
stacks = '$STACKS'.split(',')
master_dir = '$MASTER_DIR'

commands = {}
for stack in stacks:
    cmd_path = os.path.join(master_dir, 'stacks', stack.strip(), 'commands.yaml')
    if os.path.exists(cmd_path):
        with open(cmd_path) as f:
            data = yaml.safe_load(f) or {}
        for key, val in data.get('commands', {}).items():
            commands[key] = str(val)
        for key in ('classify_categories', 'critical_files', 'auto_quick_patterns'):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    commands[key.upper()] = ', '.join(str(v) for v in val)

commands['VERSION'] = '$VERSION'
commands['STACKS'] = ', '.join(stacks)

for root, dirs, files in os.walk(claude_dir):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r') as f:
            content = f.read()
        original = content
        for key, val in commands.items():
            content = content.replace('{{' + key + '}}', val)
        if content != original:
            with open(fpath, 'w') as f:
                f.write(content)
"
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

# Update workflow.lock (reuse generate_lock.py for correct masterChecksums)
echo "Updating workflow.lock..."
python3 "$MASTER_DIR/tools/generate_lock.py" \
  --claude-dir "$CLAUDE_DIR" \
  --master-dir "$MASTER_DIR" \
  --version "$VERSION" \
  --stacks "$STACKS"

echo ""
echo "$UPDATED files updated, 0 files updated" | head -1 | sed "s/0 files updated/$UPDATED files updated/"
if [[ $UPDATED -eq 0 ]] && [[ -z "$DIVERGED_FILES" ]] && [[ -z "$LOCAL_EDIT_FILES" ]]; then
  echo "Project is up to date with master v$VERSION."
fi
