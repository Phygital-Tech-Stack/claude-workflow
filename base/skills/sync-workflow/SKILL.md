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

Discover latest version from remote, compare with pinned version, clone at latest. See `reference.md` for full bash/python commands.

If `LATEST` is newer than `PINNED`, report: **Upgrade available**: pinned v{PINNED}, latest v{LATEST}.

### 3. Run Drift Check

Run `diff.sh` from cloned master against the project. Report results table. See `reference.md` for command.

### 4. Sync (if --update)

Run `sync.sh` from cloned master. See `reference.md` for command.

### 5. Clean Up

Remove `/tmp/claude-workflow-master`. See `reference.md`.

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
