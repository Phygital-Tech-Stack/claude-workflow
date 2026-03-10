---
name: sync-workflow
description: Use when workflow files may be outdated vs the master repo, or after upgrading the pinned workflow version. Syncs project files from the master claude-workflow repository.
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob
argument-hint: [--check | --update | --version <version>]
---

# /sync-workflow

**PURPOSE**: Keep project workflow files in sync with the master
claude-workflow repository.

## Modes

| Mode | What It Does |
|------|-------------|
| `--check` (default) | Run drift detection, report status |
| `--update` | Pull updates from master for BEHIND files |
| `--version <ver>` | Pin a specific version instead of auto-discovering latest |

## Steps

### 1. Check Current State

Read `.claude/workflow.lock` for pinned version and managed files.
Read `.claude/workflow.overrides.yaml` for stacks and excludes.

### 2. Discover Latest Version & Fetch Master

First, discover the latest available version from the remote repo:

```bash
MASTER_REPO="https://github.com/Phygital-Tech-Stack/claude-workflow.git"
PINNED=$(python3 -c "import json; print(json.load(open('.claude/workflow.lock'))['version'])")
LATEST=$(git ls-remote --tags --sort=-v:refname "$MASTER_REPO" 'v*' | head -1 | sed 's/.*refs\/tags\/v//')
```

If `LATEST` is newer than `PINNED`, report it to the user:
> **Upgrade available**: pinned v{PINNED}, latest v{LATEST}.

Then clone at the **latest** version (not the pinned version):

```bash
rm -rf /tmp/claude-workflow-master
git clone --depth 1 --branch "v$LATEST" "$MASTER_REPO" /tmp/claude-workflow-master
```

Update the version in `.claude/workflow.lock`:

```bash
python3 -c "
import json
lock_path = '.claude/workflow.lock'
with open(lock_path) as f:
    lock = json.load(f)
lock['version'] = '$LATEST'
with open(lock_path, 'w') as f:
    json.dump(lock, f, indent=2)
    f.write('\n')
"
```

### 3. Run Drift Check

```bash
/tmp/claude-workflow-master/tools/diff.sh --project . --master /tmp/claude-workflow-master
```

Report the results table to the user. Note: the report is now against v{LATEST}.

### 4. Sync (if --update)

```bash
/tmp/claude-workflow-master/tools/sync.sh --project . --master /tmp/claude-workflow-master
```

### 5. Clean Up

```bash
rm -rf /tmp/claude-workflow-master
```

### 6. Commit Changes

If files were updated, suggest running `/commit` with a `chore:` type.

## Related Skills

- **See also**: `/ai-guardrails-audit` for detecting drift this skill fixes
- **See also**: `/commit` for committing sync changes with `chore:` type
- **See also**: `/writing-skills audit` if synced skills need quality check

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Just copy the files manually, it's faster" | time pressure | Steps 2-3 run drift detection and diff — manual copy skips version pinning and misses conflicts |
| "Skip the cleanup step, /tmp is fine" | exhaustion | Step 5 cleanup is explicit — stale clones cause version confusion on next sync |
| "The pinned version doesn't exist in remote" | error handling | Auto-discovery fetches the latest tag from remote; falls back to pinned version if `git ls-remote` fails |
