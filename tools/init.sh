#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
PROJECT_DIR=""
STACKS=""
CI_ENABLED=false
MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=$(python3 -c "import json; print(json.load(open('$MASTER_DIR/version.json'))['version'])")

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --stacks) STACKS="$2"; shift 2 ;;
    --master) MASTER_DIR="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --ci) CI_ENABLED=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_DIR" || -z "$STACKS" ]]; then
  echo "Usage: init.sh --project <path> --stacks <stack1,stack2> [--ci]"
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

# 3. Process .mcp.json.template files from stacks (preserve project-specific servers)
echo "  Processing MCP templates..."
python3 "$MASTER_DIR/tools/merge_mcp_templates.py" \
  --stacks "$STACKS" \
  --stacks-dir "$MASTER_DIR/stacks" \
  --output "$PROJECT_DIR/.mcp.json" \
  --preserve-existing || true

# Add .mcp.json to .gitignore if not already present
if [[ -f "$PROJECT_DIR/.gitignore" ]]; then
  if ! grep -q "^\.mcp\.json$" "$PROJECT_DIR/.gitignore" 2>/dev/null; then
    echo ".mcp.json" >> "$PROJECT_DIR/.gitignore"
  fi
fi

# 4. Resolve {{PLACEHOLDER}} values from commands.yaml
echo "  Resolving placeholders..."
COMMANDS_JSON=$(python3 -c "
import os, yaml, json, sys

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

# Output commands as JSON for compose_settings.py
print(json.dumps(commands))
")

echo "  Composing settings.json..."
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

# 5. Generate workflow.lock

echo "  Generating workflow.lock..."
python3 "$MASTER_DIR/tools/generate_lock.py" \
  --claude-dir "$CLAUDE_DIR" \
  --master-dir "$MASTER_DIR" \
  --version "$VERSION" \
  --stacks "$STACKS"

# 6. Generate workflow.overrides.yaml

if [[ -f "$CLAUDE_DIR/workflow.overrides.yaml" ]]; then
  echo "  Keeping existing workflow.overrides.yaml (already exists)"
else
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
fi

# 7. Install CI templates if --ci flag was passed
if [[ "$CI_ENABLED" == "true" ]]; then
  echo "  Installing CI templates..."
  # Detect platform from git remote
  GIT_REMOTE=$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")
  if echo "$GIT_REMOTE" | grep -q "github.com"; then
    mkdir -p "$PROJECT_DIR/.github/workflows"
    cp "$MASTER_DIR/templates/github-actions/claude-pr-review.yml" \
       "$PROJECT_DIR/.github/workflows/claude-pr-review.yml"
    echo "    Installed GitHub Actions workflow: .github/workflows/claude-pr-review.yml"
    echo "    IMPORTANT: Add ANTHROPIC_API_KEY to repository secrets"
  elif echo "$GIT_REMOTE" | grep -q "gitlab"; then
    cp "$MASTER_DIR/templates/gitlab/claude-mr-review.yml" \
       "$PROJECT_DIR/.gitlab-ci-claude.yml"
    echo "    Installed GitLab CI template: .gitlab-ci-claude.yml"
    echo "    Include it in your .gitlab-ci.yml and add ANTHROPIC_API_KEY variable"
  else
    echo "    WARNING: Could not detect platform. Copy CI template manually from templates/"
  fi
fi

echo ""
echo "Done! Next steps:"
echo "  1. Edit .claude/workflow.overrides.yaml to configure excludes and settings"
echo "  2. Create .claude/project-rules.txt with project-specific rules for agents"
echo "  3. Write your project CLAUDE.md (not managed by master)"
echo "  4. Run 'tools/diff.sh' to verify zero drift"
echo "  5. Commit the .claude/ directory"
