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
LOCK_VERSION=$(python3 -c "import json; print(json.load(open('$LOCK_PATH'))['version'])")
STACKS=$(python3 -c "import json; print(','.join(json.load(open('$LOCK_PATH'))['stacks']))")
IS_SELF=$(python3 -c "import json; print(json.load(open('$LOCK_PATH')).get('self', False))")
MASTER_VERSION=$(python3 -c "import json; print(json.load(open('$MASTER_DIR/version.json'))['version'])")
VERSION="$MASTER_VERSION"

# Self-mode: .claude/ uses symlinks to base/ — only recompose settings
if [[ "$IS_SELF" == "True" ]]; then
  echo "Self-mode: .claude/ uses symlinks to base/. Re-composing settings only."

  COMMANDS_JSON=$(python3 -c "
import os, yaml, json
master_dir = '$MASTER_DIR'
cmd_path = os.path.join(master_dir, 'base', 'self-commands.yaml')
commands = {}
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
commands['STACKS'] = 'self'
print(json.dumps(commands))
")

  PRESERVE_ARGS=()
  if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    PRESERVE_ARGS+=(--preserve-from "$CLAUDE_DIR/settings.json")
  fi
  python3 "$MASTER_DIR/tools/compose_settings.py" \
    --base "$MASTER_DIR/base/settings.base.json" \
    --guards "$MASTER_DIR/base/guards" \
    --stacks "" \
    --stacks-dir "$MASTER_DIR/stacks" \
    --claude-dir "$CLAUDE_DIR" \
    --overrides "$CLAUDE_DIR/workflow.overrides.yaml" \
    --commands "$COMMANDS_JSON" \
    --output "$CLAUDE_DIR/settings.json" \
    "${PRESERVE_ARGS[@]}"

  python3 "$MASTER_DIR/tools/generate_lock.py" \
    --claude-dir "$CLAUDE_DIR" \
    --master-dir "$MASTER_DIR" \
    --version "$VERSION" \
    --stacks "" \
    --self

  echo "Settings recomposed. Lock updated to v$VERSION."
  exit 0
fi

echo "Syncing project at $PROJECT_DIR (pinned: v$LOCK_VERSION → v$VERSION, stacks: $STACKS)"

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
import sys; sys.path.insert(0, '$MASTER_DIR/tools')
from workflow_utils import find_master_source
r = find_master_source('$MASTER_DIR', '$file', '$STACKS'.split(','))
if r: print(r)
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
import sys; sys.path.insert(0, '$MASTER_DIR/tools')
from workflow_utils import find_master_source
r = find_master_source('$MASTER_DIR', '$file', '$STACKS'.split(','))
if r: print(r)
")
    if [[ -n "$SOURCE" ]]; then
      mkdir -p "$(dirname "$CLAUDE_DIR/$file")"
      cp "$SOURCE" "$CLAUDE_DIR/$file"
      UPDATED=$((UPDATED + 1))
    fi
  done <<< "$MISSING_FILES"
fi

# Detect NEW files in master that aren't in the lock yet
echo ""
echo "Checking for new files in master..."
NEW_FILES=$(python3 -c "
import json, os, sys

lock_path = '$LOCK_PATH'
master_dir = '$MASTER_DIR'
claude_dir = '$CLAUDE_DIR'
stacks = '$STACKS'.split(',')

with open(lock_path) as f:
    lock = json.load(f)
managed = set(lock.get('managed', {}).keys())

# Load excludes from overrides
excludes = set()
overrides_path = os.path.join(claude_dir, 'workflow.overrides.yaml')
if os.path.exists(overrides_path):
    try:
        import yaml
        with open(overrides_path) as f:
            overrides = yaml.safe_load(f) or {}
        excludes = set(overrides.get('exclude', []) or [])
    except ImportError:
        pass

def is_excluded(rel_path):
    return any(rel_path.startswith(ex.rstrip('/')) for ex in excludes)

# Scan base for files not in lock
scan_dirs = {
    'base/hooks': 'hooks',
    'base/agents': 'agents',
    'base/skills': 'skills',
    'base/blueprints': 'blueprints',
    'base/teams': 'teams',
}
# Also add WORKFLOW.md
base_wf = os.path.join(master_dir, 'base', 'WORKFLOW.md')
if os.path.exists(base_wf) and 'WORKFLOW.md' not in managed:
    print('WORKFLOW.md')

for src_dir_rel, dest_prefix in scan_dirs.items():
    src_dir = os.path.join(master_dir, src_dir_rel)
    if not os.path.isdir(src_dir):
        continue
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            src_path = os.path.join(root, fname)
            rel_from_src = os.path.relpath(src_path, src_dir)
            dest_rel = os.path.join(dest_prefix, rel_from_src)
            if dest_rel not in managed and not is_excluded(dest_rel):
                # Skip __pycache__ and .pyc files
                if '__pycache__' in dest_rel or dest_rel.endswith('.pyc'):
                    continue
                print(dest_rel)

# Scan stack dirs for new files
for stack in stacks:
    stack = stack.strip()
    for sub in ('hooks', 'failure-patterns'):
        src_dir = os.path.join(master_dir, 'stacks', stack, sub)
        if not os.path.isdir(src_dir):
            continue
        dest_prefix = 'hooks' if sub == 'hooks' else 'hooks/failure-patterns'
        for root, dirs, files in os.walk(src_dir):
            for fname in files:
                src_path = os.path.join(root, fname)
                if sub == 'failure-patterns':
                    dest_rel = os.path.join(dest_prefix, fname)
                else:
                    rel_from_src = os.path.relpath(src_path, src_dir)
                    dest_rel = os.path.join(dest_prefix, rel_from_src)
                if dest_rel not in managed and not is_excluded(dest_rel):
                    if '__pycache__' in dest_rel or dest_rel.endswith('.pyc'):
                        continue
                    print(dest_rel)

    # Scan stack teams for new files
    teams_dir = os.path.join(master_dir, 'stacks', stack, 'teams')
    if os.path.isdir(teams_dir):
        for root, dirs, files in os.walk(teams_dir):
            for fname in files:
                src_path = os.path.join(root, fname)
                rel_from_teams = os.path.relpath(src_path, teams_dir)
                dest_rel = os.path.join('teams', rel_from_teams)
                if dest_rel not in managed and not is_excluded(dest_rel):
                    if '__pycache__' in dest_rel or dest_rel.endswith('.pyc'):
                        continue
                    print(dest_rel)
" 2>/dev/null) || true

if [[ -n "$NEW_FILES" ]]; then
  echo "NEW files from master (will add):"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    echo "  Adding: $file"
    SOURCE=$(python3 -c "
import sys; sys.path.insert(0, '$MASTER_DIR/tools')
from workflow_utils import find_master_source
r = find_master_source('$MASTER_DIR', '$file', '$STACKS'.split(','))
if r: print(r)
")
    if [[ -n "$SOURCE" ]]; then
      mkdir -p "$(dirname "$CLAUDE_DIR/$file")"
      cp "$SOURCE" "$CLAUDE_DIR/$file"
      # Make shell scripts executable
      if [[ "$file" == *.sh ]]; then
        chmod +x "$CLAUDE_DIR/$file"
      fi
      UPDATED=$((UPDATED + 1))
    fi
  done <<< "$NEW_FILES"
fi

# Build commands JSON for placeholder resolution
COMMANDS_JSON=$(python3 -c "
import sys, json; sys.path.insert(0, '$MASTER_DIR/tools')
from workflow_utils import load_commands
print(json.dumps(load_commands('$MASTER_DIR', '$STACKS'.split(','), '$VERSION')))
")

# Resolve {{PLACEHOLDER}} values in updated .md files
if [[ $UPDATED -gt 0 ]]; then
  echo ""
  echo "Resolving placeholders..."
  python3 -c "
import os, json

claude_dir = '$CLAUDE_DIR'
commands = json.loads('$COMMANDS_JSON')

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

# Recompose settings.json (always run to ensure overrides are applied)
echo ""
echo "Recomposing settings.json..."
PRESERVE_ARGS=()
if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
  PRESERVE_ARGS+=(--preserve-from "$CLAUDE_DIR/settings.json")
fi
python3 "$MASTER_DIR/tools/compose_settings.py" \
  --base "$MASTER_DIR/base/settings.base.json" \
  --guards "$MASTER_DIR/base/guards" \
  --stacks "$STACKS" \
  --stacks-dir "$MASTER_DIR/stacks" \
  --claude-dir "$CLAUDE_DIR" \
  --overrides "$CLAUDE_DIR/workflow.overrides.yaml" \
  --commands "$COMMANDS_JSON" \
  --output "$CLAUDE_DIR/settings.json" \
  "${PRESERVE_ARGS[@]}"

# Re-process MCP templates (preserve project-specific servers)
echo "Re-processing MCP templates..."
python3 "$MASTER_DIR/tools/merge_mcp_templates.py" \
  --stacks "$STACKS" \
  --stacks-dir "$MASTER_DIR/stacks" \
  --output "$PROJECT_DIR/.mcp.json" \
  --preserve-existing || true

# Update workflow.lock (reuse generate_lock.py for correct masterChecksums)
echo "Updating workflow.lock..."
python3 "$MASTER_DIR/tools/generate_lock.py" \
  --claude-dir "$CLAUDE_DIR" \
  --master-dir "$MASTER_DIR" \
  --version "$VERSION" \
  --stacks "$STACKS"

echo ""
echo "$UPDATED file(s) updated."
if [[ $UPDATED -eq 0 ]] && [[ -z "$DIVERGED_FILES" ]] && [[ -z "$LOCAL_EDIT_FILES" ]]; then
  echo "Project is up to date with master v$VERSION."
fi
