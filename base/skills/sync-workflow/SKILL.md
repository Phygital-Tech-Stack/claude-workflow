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
| `--version <ver>` | Update pinned version in overrides, then sync |

## Steps

### 1. Check Current State

Read `.claude/workflow.lock` for pinned version and managed files.
Read `.claude/workflow.overrides.yaml` for stacks and excludes.

### 2. Fetch Master

Clone/fetch the master repo at the pinned version:

```bash
MASTER_REPO="https://github.com/Phygital-Tech-Stack/claude-workflow.git"
VERSION=$(python3 -c "import json; print(json.load(open('.claude/workflow.lock'))['version'])")
git clone --depth 1 --branch "v$VERSION" "$MASTER_REPO" /tmp/claude-workflow-master
```

### 3. Run Drift Check

```bash
/tmp/claude-workflow-master/tools/diff.sh --project . --master /tmp/claude-workflow-master
```

Report the results table to the user.

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
| "The pinned version doesn't exist in remote" | error handling | Clone command will fail visibly; user must fix version in `.claude/workflow.lock` before retrying |
