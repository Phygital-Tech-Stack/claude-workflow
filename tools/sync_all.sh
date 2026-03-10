#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# sync_all.sh — Sync all managed projects to current master version
#
# Operates on local project checkouts under --projects-dir (default: ../),
# the sibling directory of the claude-workflow master repo.
#
# For each project in projects.json:
#   1. Locate local checkout under projects-dir
#   2. Determine tier: sync-only vs init-needed
#   3. Run sync.sh or init.sh
#   4. Generate workflow.overrides.yaml for special-case repos
#   5. Create branch, commit, push, open PR
#
# Usage:
#   tools/sync_all.sh [--dry-run] [--repo <name>] [--projects-dir <path>]
#
# Options:
#   --dry-run          Print what would be done without executing
#   --repo <name>      Only sync a single repo (e.g. "phast", "erp")
#   --projects-dir     Root dir containing all project checkouts (default: parent of master)
###############################################################################

MASTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=$(python3 -c "import json; print(json.load(open('$MASTER_DIR/version.json'))['version'])")
BRANCH="chore/workflow-v${VERSION}"
DRY_RUN=false
SINGLE_REPO=""
PROJECTS_DIR="$(cd "$MASTER_DIR/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)        DRY_RUN=true; shift ;;
    --repo)           SINGLE_REPO="$2"; shift 2 ;;
    --projects-dir)   PROJECTS_DIR="$2"; shift 2 ;;
    *)                echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo "=== sync_all.sh — master v${VERSION} ==="
echo "    Branch: $BRANCH"
echo "    Projects dir: $PROJECTS_DIR"
echo "    Dry run: $DRY_RUN"
echo ""

# Read projects from projects.json
PROJECTS=$(python3 -c "
import json
with open('$MASTER_DIR/projects.json') as f:
    data = json.load(f)
for p in data['projects']:
    name = p['repo'].split('/')[-1]
    stacks = ','.join(p['stacks'])
    print(f\"{p['repo']}|{name}|{stacks}\")
")

# Track results
SUCCEEDED=()
FAILED=()
SKIPPED=()

# ─── Per-repo overrides for special cases ────────────────────────────────────

generate_overrides_erp() {
  local claude_dir="$1"
  cat > "$claude_dir/workflow.overrides.yaml" << 'YAML'
# Claude Workflow Overrides — erp
# Project-specific files excluded from master sync

version: "${VERSION}"
stacks:
  - typescript-nestjs

exclude:
  # Project-specific skills
  - skills/debug/
  - skills/generate-endpoint/
  - skills/generate-module/
  - skills/guardrail-radar/
  - skills/impact-analysis/
  - skills/test-runner/
  - skills/ui-ux-pro-max/
  # Project-specific agents (customized with ERP domain knowledge)
  - agents/architecture-guardian.md
  - agents/database-expert.md
  - agents/security-reviewer.md
  - agents/code-reviewer.md
  # Project-specific content
  - blueprints/
  - rules/
  - teams/
  # Project-specific hooks
  - hooks/check_schema_fields.py
  - hooks/check_cross_module.py
  - hooks/check_config_first.py
  - hooks/check_zustand_purity.py
  - hooks/check_claude_md_size.py
  - hooks/check_function_length.py
  - hooks/check_as_warning.py
  - hooks/check_any_blocker.py
  - hooks/check_file_size.py
YAML
}

generate_overrides_phronesis() {
  local claude_dir="$1"
  cat > "$claude_dir/workflow.overrides.yaml" << 'YAML'
# Claude Workflow Overrides — phronesis
# Project-specific files excluded from master sync

version: "${VERSION}"
stacks:
  - python-fastapi

exclude:
  - commands/
YAML
}

# ─── Tier classification ─────────────────────────────────────────────────────

classify_tier() {
  local project_dir="$1"
  local name="$2"
  local claude_dir="$project_dir/.claude"

  # Special cases first
  if [[ "$name" == "erp" ]]; then
    echo "3-erp"
    return
  fi
  if [[ "$name" == "phronesis" ]]; then
    echo "3-phronesis"
    return
  fi

  # Tier 1: has workflow.lock + settings.json with hook events → sync only
  if [[ -f "$claude_dir/workflow.lock" ]] && [[ -f "$claude_dir/settings.json" ]]; then
    local has_hooks
    has_hooks=$(python3 -c "
import json, sys
try:
    data = json.load(open('$claude_dir/settings.json'))
    hooks = data.get('hooks', {})
    if any(k in hooks for k in ['PreToolUse', 'PostToolUse', 'SessionStart', 'UserPromptSubmit']):
        print('yes')
    else:
        print('no')
except: print('no')
" 2>/dev/null)
    if [[ "$has_hooks" == "yes" ]]; then
      echo "1"
      return
    fi
  fi

  # Tier 2: has workflow.lock but missing/incomplete settings
  if [[ -f "$claude_dir/workflow.lock" ]]; then
    echo "2"
    return
  fi

  # No lock at all — treat as tier 2 (init)
  echo "2"
}

# ─── Process a single project ────────────────────────────────────────────────

process_project() {
  local repo="$1"
  local name="$2"
  local stacks="$3"
  local project_dir="$PROJECTS_DIR/$name"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Processing: $name ($repo) — stacks: $stacks"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Verify local checkout exists
  if [[ ! -d "$project_dir/.git" ]]; then
    echo "  ERROR: No git repo found at $project_dir"
    return 1
  fi

  # Classify tier
  local tier
  tier=$(classify_tier "$project_dir" "$name")

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  Path: $project_dir"
    echo "  Tier: $tier"
    echo "  [DRY RUN] Would create branch $BRANCH"
    case "$tier" in
      1)
        echo "  [DRY RUN] Would run: sync.sh --project $project_dir --master $MASTER_DIR --auto"
        ;;
      2|3-*)
        echo "  [DRY RUN] Would run: init.sh --project $project_dir --stacks $stacks --master $MASTER_DIR"
        if [[ "$tier" == "3-erp" ]]; then
          echo "  [DRY RUN] Would generate erp-specific workflow.overrides.yaml"
        elif [[ "$tier" == "3-phronesis" ]]; then
          echo "  [DRY RUN] Would generate phronesis-specific workflow.overrides.yaml"
        fi
        ;;
    esac
    echo "  [DRY RUN] Would commit, push, and create PR"
    return 0
  fi

  # Ensure we're on main/master and up to date
  echo "  Ensuring clean state on default branch..."
  cd "$project_dir"
  local default_branch
  default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
  # Stash any uncommitted changes to allow branch switching
  git stash -q 2>/dev/null || true
  git checkout "$default_branch" 2>/dev/null || git checkout main 2>/dev/null || git checkout master 2>/dev/null
  git pull --ff-only 2>/dev/null || true

  # Delete existing branch if it exists (start fresh)
  git branch -D "$BRANCH" 2>/dev/null || true

  # Create branch
  echo "  Creating branch $BRANCH..."
  git checkout -b "$BRANCH" || {
    echo "  ERROR: Failed to create branch"
    return 1
  }

  # Save original settings.json before any sync/init modifies it.
  # Used by validate_sync.py to detect lost permissions/MCP servers,
  # and by Tier 3 re-compose to avoid duplicating inline hooks.
  local original_settings=""
  if [[ -f "$project_dir/.claude/settings.json" ]]; then
    original_settings=$(mktemp)
    cp "$project_dir/.claude/settings.json" "$original_settings"
  fi

  # Run appropriate tool
  echo "  Tier: $tier"

  case "$tier" in
    1)
      echo "  Running sync.sh (Tier 1: clean sync)..."
      "$MASTER_DIR/tools/sync.sh" \
        --project "$project_dir" \
        --master "$MASTER_DIR" \
        --auto
      ;;
    2)
      echo "  Running init.sh (Tier 2: re-init)..."
      "$MASTER_DIR/tools/init.sh" \
        --project "$project_dir" \
        --stacks "$stacks" \
        --master "$MASTER_DIR"
      ;;
    3-erp)
      # Generate overrides BEFORE init.sh so it can read the exclude list
      # and skip project-specific files (agents, skills, blueprints, etc.)
      echo "  Generating erp-specific workflow.overrides.yaml..."
      mkdir -p "$project_dir/.claude"
      generate_overrides_erp "$project_dir/.claude"
      echo "  Running init.sh (Tier 3: erp special case)..."
      "$MASTER_DIR/tools/init.sh" \
        --project "$project_dir" \
        --stacks "$stacks" \
        --master "$MASTER_DIR"
      # Re-compose settings with overrides applied
      # Uses the ORIGINAL settings.json (saved before init.sh) for --preserve-from
      # so project-specific inline hooks are preserved exactly once.
      echo "  Re-composing settings.json with overrides..."
      local commands_json
      commands_json=$(python3 -c "
import os, yaml, json
stacks = '$stacks'.split(',')
commands = {}
for stack in stacks:
    cmd_path = os.path.join('$MASTER_DIR', 'stacks', stack.strip(), 'commands.yaml')
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
print(json.dumps(commands))
")
      local preserve_args=()
      if [[ -n "$original_settings" ]]; then
        preserve_args+=(--preserve-from "$original_settings")
      fi
      python3 "$MASTER_DIR/tools/compose_settings.py" \
        --base "$MASTER_DIR/base/settings.base.json" \
        --guards "$MASTER_DIR/base/guards" \
        --stacks "$stacks" \
        --stacks-dir "$MASTER_DIR/stacks" \
        --claude-dir "$project_dir/.claude" \
        --overrides "$project_dir/.claude/workflow.overrides.yaml" \
        --commands "$commands_json" \
        --output "$project_dir/.claude/settings.json" \
        "${preserve_args[@]}"
      # Regenerate lock with overrides in place
      python3 "$MASTER_DIR/tools/generate_lock.py" \
        --claude-dir "$project_dir/.claude" \
        --master-dir "$MASTER_DIR" \
        --version "$VERSION" \
        --stacks "$stacks"
      ;;
    3-phronesis)
      echo "  Generating phronesis-specific workflow.overrides.yaml..."
      mkdir -p "$project_dir/.claude"
      generate_overrides_phronesis "$project_dir/.claude"
      echo "  Running init.sh (Tier 3: phronesis special case)..."
      "$MASTER_DIR/tools/init.sh" \
        --project "$project_dir" \
        --stacks "$stacks" \
        --master "$MASTER_DIR"
      # Regenerate lock with overrides in place
      python3 "$MASTER_DIR/tools/generate_lock.py" \
        --claude-dir "$project_dir/.claude" \
        --master-dir "$MASTER_DIR" \
        --version "$VERSION" \
        --stacks "$stacks"
      ;;
  esac

  # Check for changes
  if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
    echo "  No changes detected — skipping"
    git checkout "$default_branch" 2>/dev/null || git checkout main 2>/dev/null
    git branch -D "$BRANCH" 2>/dev/null || true
    [[ -n "$original_settings" ]] && rm -f "$original_settings"
    return 2  # Signal: skipped
  fi

  # Validate before committing
  echo "  Running post-sync validation..."
  local validate_args=(
    --claude-dir "$project_dir/.claude"
    --expected-version "$VERSION"
  )
  if [[ -n "$original_settings" ]]; then
    validate_args+=(--original-settings "$original_settings")
  fi
  if ! python3 "$MASTER_DIR/tools/validate_sync.py" "${validate_args[@]}"; then
    echo "  VALIDATION FAILED — aborting sync for $name"
    git checkout "$default_branch" 2>/dev/null || git checkout main 2>/dev/null
    git branch -D "$BRANCH" 2>/dev/null || true
    [[ -n "$original_settings" ]] && rm -f "$original_settings"
    return 1
  fi

  # Clean up original settings temp file
  [[ -n "$original_settings" ]] && rm -f "$original_settings"

  # Commit
  echo "  Staging and committing..."
  chmod +x "$project_dir/.claude/hooks/"*.sh 2>/dev/null || true
  git add .claude/
  # Force executable bit in git index for all hook scripts
  # (lint-staged stash/restore can strip filesystem +x before commit)
  for hook_file in .claude/hooks/*.sh; do
    [[ -f "$hook_file" ]] && git update-index --chmod=+x "$hook_file" 2>/dev/null || true
  done
  # Untrack .mcp.json if it was previously tracked (contains credentials)
  if git ls-files --error-unmatch .mcp.json 2>/dev/null; then
    echo "  Untracking .mcp.json (should not be committed — may contain credentials)"
    git rm --cached .mcp.json 2>/dev/null || true
  fi
  # Stage .gitignore if modified
  git diff --quiet .gitignore 2>/dev/null || git add .gitignore 2>/dev/null || true

  git commit -m "$(cat <<EOF
chore: sync claude-workflow to v${VERSION}

Update .claude/ configuration from claude-workflow master v${VERSION}.
Includes new hooks, agents, guards, and settings composition.

Managed by: https://github.com/Phygital-Tech-Stack/claude-workflow
EOF
  )"

  # Push
  echo "  Pushing branch..."
  git fetch origin 2>/dev/null || true
  git push -u origin "$BRANCH" --force-with-lease 2>&1

  # Create PR
  echo "  Creating PR..."
  local pr_body
  pr_body=$(cat <<EOF
## Summary
- Sync \`.claude/\` workflow configuration to master **v${VERSION}**
- Tier: ${tier} — $(case "$tier" in 1) echo "clean sync (sync.sh)";; 2) echo "re-init (init.sh)";; 3-*) echo "special handling (init.sh + overrides)";; esac)

## What changed
- \`workflow.lock\` version bumped to \`${VERSION}\`
- New/updated hooks: \`prompt-submit.sh\`, \`stop-gate.sh\`, \`context-check.sh\`
- New agents: \`planner.md\`, \`backend-handler.md\`, \`frontend-handler.md\`, \`test-writer.md\`, \`security-reviewer.md\`, \`db-expert.md\`
- \`settings.json\` recomposed with \`UserPromptSubmit\` and \`Stop\` events
- \`.mcp.json\` template generated for stack: \`${stacks}\`

## Verification
- [ ] \`workflow.lock\` shows version \`${VERSION}\`
- [ ] \`settings.json\` has \`UserPromptSubmit\` and \`Stop\` hook events
- [ ] Project-specific files are NOT overwritten
- [ ] Run \`/sync-workflow --check\` from within repo to confirm zero drift

Managed by [claude-workflow](https://github.com/Phygital-Tech-Stack/claude-workflow)
EOF
  )

  local pr_url
  pr_url=$(gh pr create \
    --title "chore: sync claude-workflow to v${VERSION}" \
    --body "$pr_body" \
    --base "$default_branch" 2>&1) || {
    # PR might already exist
    echo "  WARNING: PR creation failed (may already exist)"
    pr_url="(existing)"
  }
  echo "  PR: $pr_url"

  return 0
}

# ─── Main loop ────────────────────────────────────────────────────────────────

while IFS='|' read -r repo name stacks; do
  # Filter by --repo if specified
  if [[ -n "$SINGLE_REPO" ]] && [[ "$name" != "$SINGLE_REPO" ]]; then
    continue
  fi

  result=0
  process_project "$repo" "$name" "$stacks" || result=$?

  case $result in
    0) SUCCEEDED+=("$name") ;;
    2) SKIPPED+=("$name") ;;
    *) FAILED+=("$name") ;;
  esac

  echo ""
done <<< "$PROJECTS"

# ─── Summary ─────────────────────────────────────────────────────────────────

echo "================================================================"
echo "sync_all.sh complete — master v${VERSION}"
echo "================================================================"
echo ""
if [[ ${#SUCCEEDED[@]} -gt 0 ]]; then
  echo "  Succeeded (${#SUCCEEDED[@]}): ${SUCCEEDED[*]}"
fi
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
  echo "  Skipped   (${#SKIPPED[@]}): ${SKIPPED[*]}"
fi
if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "  Failed    (${#FAILED[@]}): ${FAILED[*]}"
  echo ""
  echo "  Fix issues and re-run with --repo <name> to retry individual repos."
  exit 1
fi

# ─── Warnings ─────────────────────────────────────────────────────────────────

echo ""
echo "Reminders:"
echo "  - www: Missing root CLAUDE.md — project owner should create manually"
echo "  - erp: Inline guards replaced by compose_settings.py output — verify PR diff"
echo "  - Review each PR before merging"
echo "  - After merge, run /sync-workflow --check in each repo to confirm zero drift"
