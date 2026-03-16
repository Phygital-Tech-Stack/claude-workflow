# Hook Expansion: SessionEnd, SubagentStop, MCP Security Scan

**Date**: 2026-03-16
**Issues**: #15, #16, #23
**Status**: Approved — ready for implementation

## Context

Brainstorm verified available Claude Code event types against docs. Of 8 proposed issues (#14-21, #23), only 3 have confirmed event types. The rest (#14 PostCompact, #20 WorktreeCreate/Remove, #21 ConfigChange) are deferred — their event types don't exist in Claude Code yet. #19 (HTTP hooks) needs separate investigation.

### Confirmed Event Types (from Claude Code docs)

`PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SessionEnd vs Stop | Merge into one SessionEnd hook | Stop and SessionEnd are functionally equivalent; no need for both |
| SubagentStop strictness | Steer (warn only) | Follows steer-dont-block pattern (#24) |
| MCP scan trigger | SessionStart | One-time per session; lower cost than per-tool-call |

## Changes

### 1. SessionEnd Hook (#15) — replaces Stop

**New file**: `base/hooks/session-end.sh`
**Removes**: `base/hooks/stop-gate.sh`

Logic:
1. Read `session-files-*.txt` → count modified code files
2. `git status --porcelain` → detect uncommitted changes
3. If code files modified but not committed → `[STEER]` warning
4. Log to `.claude/session-metrics.log`: timestamp, files_modified, uncommitted flag
5. Exit 0 always

Settings: Replace `Stop` event with `SessionEnd` in `settings.base.json`.

### 2. SubagentStop Hook (#16)

**New file**: `base/hooks/subagent-stop.sh`

Logic:
1. Read stdin JSON for subagent output
2. Check if output empty or <10 chars
3. Check for failure patterns (traceback, error, timeout, "I couldn't")
4. If suspect → `[STEER] Subagent output may be incomplete`
5. Exit 0 always

Settings: Add `SubagentStop` event to `settings.base.json`.

### 3. MCP Security Scan (#23)

**New file**: `base/hooks/mcp-security-scan.sh`

Logic:
1. Find `.mcp.json` in project root
2. Parse server entries (Python one-liner)
3. Flag: no auth tokens, write-capable unvetted servers
4. Emit `[SECURITY]` warning per finding
5. Exit 0 (steer)

Settings: Add to `SessionStart` array in `settings.base.json`.

### 4. WORKFLOW.md Updates

- Replace "Stop gate" row with "Session end" in lifecycle hooks table
- Add "Subagent stop" row
- Add "MCP security scan" row

### 5. Deferred Issues

| Issue | Reason | Action |
|-------|--------|--------|
| #14 PostCompact | Event type doesn't exist | Label `blocked:upstream`, close |
| #19 HTTP hooks | Not in Claude Code docs | Label `needs-investigation`, keep open |
| #20 WorktreeCreate/Remove | Event type doesn't exist | Label `blocked:upstream`, close |
| #21 ConfigChange | Event type doesn't exist | Label `blocked:upstream`, close |

## Verification

1. Start a new session → MCP security scan fires, check for `[SECURITY]` output
2. Run a subagent → SubagentStop fires on completion
3. End session → SessionEnd fires with metrics + uncommitted warning
4. Confirm `stop-gate.sh` removed, no regressions
5. Check `.claude/session-metrics.log` created after session end
