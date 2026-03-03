#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
PROJECT_DIR=""
STACKS=""
MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=$(python3 -c "import json; print(json.load(open('$MASTER_DIR/version.json'))['version'])")

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --stacks) STACKS="$2"; shift 2 ;;
    --master) MASTER_DIR="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_DIR" || -z "$STACKS" ]]; then
  echo "Usage: init.sh --project <path> --stacks <stack1,stack2>"
  exit 1
fi

CLAUDE_DIR="$PROJECT_DIR/.claude"
mkdir -p "$CLAUDE_DIR"/{hooks,skills,agents,blueprints,agent-memory,progress}

echo "Initializing project at $PROJECT_DIR with stacks: $STACKS (master v$VERSION)"

# 1. Copy base files
echo "  Copying base files..."
cp "$MASTER_DIR/base/WORKFLOW.md" "$CLAUDE_DIR/WORKFLOW.md"
cp "$MASTER_DIR/base/hooks/"*.sh "$CLAUDE_DIR/hooks/"
chmod +x "$CLAUDE_DIR/hooks/"*.sh

# Copy base skills (skip empty directories)
for skill_dir in "$MASTER_DIR/base/skills/"*/; do
  skill_name=$(basename "$skill_dir")
  # Only copy if directory contains files
  if compgen -G "$skill_dir"* > /dev/null 2>&1; then
    mkdir -p "$CLAUDE_DIR/skills/$skill_name"
    cp "$skill_dir"* "$CLAUDE_DIR/skills/$skill_name/"
  fi
done

# Copy base agents
cp "$MASTER_DIR/base/agents/"*.md "$CLAUDE_DIR/agents/"

# Copy base blueprints
for tmpl in "$MASTER_DIR/base/blueprints/"*.template.md; do
  basename_no_template=$(basename "$tmpl" .template.md)
  cp "$tmpl" "$CLAUDE_DIR/blueprints/${basename_no_template}.md"
done

# 2. Apply stack overlays
IFS=',' read -ra STACK_ARRAY <<< "$STACKS"
for stack in "${STACK_ARRAY[@]}"; do
  stack_dir="$MASTER_DIR/stacks/$stack"
  if [[ ! -d "$stack_dir" ]]; then
    echo "  WARNING: Stack '$stack' not found at $stack_dir"
    continue
  fi

  echo "  Applying stack: $stack"

  # Copy stack hooks
  if [[ -d "$stack_dir/hooks" ]]; then
    cp "$stack_dir/hooks/"* "$CLAUDE_DIR/hooks/" 2>/dev/null || true
    chmod +x "$CLAUDE_DIR/hooks/"*.sh 2>/dev/null || true
  fi

  # Copy failure patterns
  if [[ -d "$stack_dir/failure-patterns" ]]; then
    mkdir -p "$CLAUDE_DIR/hooks/failure-patterns"
    cp "$stack_dir/failure-patterns/"* "$CLAUDE_DIR/hooks/failure-patterns/"
  fi
done

# 3. Resolve {{PLACEHOLDER}} values from commands.yaml
echo "  Resolving placeholders..."
python3 -c "
import os, yaml, re, sys

claude_dir = '$CLAUDE_DIR'
stacks = '$STACKS'.split(',')
master_dir = '$MASTER_DIR'

# Collect all command values from all stacks
commands = {}
for stack in stacks:
    cmd_path = os.path.join(master_dir, 'stacks', stack.strip(), 'commands.yaml')
    if os.path.exists(cmd_path):
        with open(cmd_path) as f:
            data = yaml.safe_load(f) or {}
        for key, val in data.get('commands', {}).items():
            commands[key] = str(val)
        # Also resolve list-based values
        for key in ('classify_categories', 'critical_files', 'auto_quick_patterns'):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    commands[key.upper()] = ', '.join(str(v) for v in val)

# Also add VERSION and STACKS
commands['VERSION'] = '$VERSION'
commands['STACKS'] = ', '.join(stacks)

# Walk all .md files and resolve placeholders
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

echo "  Composing settings.json..."
python3 "$MASTER_DIR/tools/compose_settings.py" \
  --base "$MASTER_DIR/base/settings.base.json" \
  --guards "$MASTER_DIR/base/guards" \
  --stacks "$STACKS" \
  --stacks-dir "$MASTER_DIR/stacks" \
  --output "$CLAUDE_DIR/settings.json"

# 4. Generate workflow.lock

echo "  Generating workflow.lock..."
python3 -c "
import json, hashlib, os, sys
from datetime import datetime, timezone

claude_dir = '$CLAUDE_DIR'
version = '$VERSION'
stacks = '$STACKS'.split(',')

managed = {}
for root, dirs, files in os.walk(claude_dir):
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, claude_dir)
        # Skip project-owned files
        if rel.startswith(('agent-memory/', 'progress/', 'session-files', 'decisions.log', 'compaction.log')):
            continue
        if rel in ('settings.local.json', 'project-rules.txt'):
            continue
        with open(full, 'rb') as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        managed[rel] = f'sha256:{sha}'

lock = {
    'version': version,
    'stacks': stacks,
    'lastSync': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    'managed': managed
}

with open(os.path.join(claude_dir, 'workflow.lock'), 'w') as f:
    json.dump(lock, f, indent=2)
    f.write('\n')
"

# 5. Generate workflow.overrides.yaml

echo "  Generating workflow.overrides.yaml..."
cat > "$CLAUDE_DIR/workflow.overrides.yaml" << EOF
# Claude Workflow Overrides
# See: https://github.com/Phygital-Tech-Stack/claude-workflow

version: "$VERSION"
stacks:
$(for stack in "${STACK_ARRAY[@]}"; do echo "  - $stack"; done)

# Files to exclude from master sync (project-owned)
exclude: []
  # - skills/my-custom-skill/
  # - agents/my-custom-agent.md

# Additional settings merged on top of base + stack
# settings:
#   permissions:
#     allow:
#       - "Bash(my-tool:*)"

# Blueprint overrides (project-specific sections)
# blueprints:
#   coding-conventions:
#     tech_specific: |
#       ### Project-Specific Conventions
#       - Add your conventions here
EOF

echo ""
echo "Done! Next steps:"
echo "  1. Edit .claude/workflow.overrides.yaml to configure excludes and settings"
echo "  2. Create .claude/project-rules.txt with project-specific rules for agents"
echo "  3. Write your project CLAUDE.md (not managed by master)"
echo "  4. Run 'tools/diff.sh' to verify zero drift"
echo "  5. Commit the .claude/ directory"
