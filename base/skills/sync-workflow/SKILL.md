---
name: sync-workflow
description: Sync project workflow files from master claude-workflow repo. Use when updating to latest workflow version or checking for drift.
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
