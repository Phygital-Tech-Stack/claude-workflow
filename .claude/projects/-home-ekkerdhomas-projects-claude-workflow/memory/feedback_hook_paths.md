---
name: Hook commands must use absolute paths
description: Claude Code hooks using relative .claude/hooks/ paths break when CWD changes (e.g. cd backend). Use $(git rev-parse --show-toplevel) to resolve absolute paths.
type: feedback
---

Hook commands in settings.json must use absolute paths, not relative `.claude/hooks/` references.

**Why:** Claude Code's hook runner inherits the shell's CWD. If any command during a session changes CWD (e.g. `cd backend` for `dart test`), relative paths like `.claude/hooks/pyrun` resolve against the new CWD and fail — causing *all* hooks to error silently.

**How to apply:** When writing or updating hook commands in settings.json, always prefix hook paths with `$(git rev-parse --show-toplevel)/.claude/hooks/` so they resolve correctly regardless of CWD. Also ensure helper scripts like `pyrun` `cd` to the repo root before running.
