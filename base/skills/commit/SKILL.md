---
name: commit
description: Use when committing code changes after a work session.
user-invocable: true
argument-hint: [--all | --amend]
allowed-tools: Bash, Read, Grep, Glob, Edit, Task, Agent
---

# Smart Commit Command

**PURPOSE**: Create quality commits with session-scoped staging, lattice-gated validation, and conventional commit formatting.

## File Tracking (Compression-Proof)

A PostToolUse hook logs every file path touched by Write/Edit to `.claude/session-files-<session_id>.txt`. Use `--all` to stage everything instead.

## Steps

### Pre-Commit (delegated to Sonnet agent)

Spawn an Agent (`subagent_type: "general-purpose"`, `model: "sonnet"`) to run:
- **Step 1**: Identify changes (`git status` + session files)
- **Step 2**: Documentation check (scan for CLAUDE.md drift)
- **Step 2.5**: Lattice gate check (verify `/validate-change` ran)
- **Step 2.7**: Task completion check (progress file unchecked steps)
- **Step 4**: Format and analyze (`dart format`, `flutter analyze`)

Agent returns: file list, gate status, warnings, format/analyze results.

See `reference.md` "Pre-Commit Agent Prompt Template" for the exact agent prompt.

### Main Context (Opus)

- Review pre-commit agent results
- **Step 3**: Code review via `code-reviewer` agent (Sonnet) -- skip if `/validate-change` already ran this session (L4 covers it)
- **Step 5**: Generate conventional commit message, confirm with user, execute commit

Generate conventional commit with `Co-Authored-By` trailer. **Types**: feat, fix, refactor, style, test, docs, chore, perf.

### Post-Commit (delegated to Sonnet agent)

Spawn an Agent (`subagent_type: "general-purpose"`, `model: "sonnet"`) to run:
- **Step 5.5**: Update progress file in `3-in-progress/`
- **Step 5.7**: Archive completed plans to `4-done/`
- **Step 7**: Write session progress file
- **Step 7.5**: Append to decision log
- **Step 8**: Clean up tracking file

See `reference.md` "Post-Commit Agent Prompt Template" for the exact agent prompt.

### Verify

```bash
git log -1 --stat
```

See `reference.md` for common mistakes and error handling.

## Related Skills

- **REQUIRED**: `/validate-change` — MUST run before commit (hard gate)
- **See also**: `/tdd` for test-driven implementation before committing
- **See also**: `/brainstorm` for design decisions before implementation
- **See also**: `/security` for standalone security checks

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Just commit everything, I'll review later" | time + sunk cost | Lattice check (Step 2.5) is a HARD GATE — blocks commit without `/validate-change` |
| "Commit but skip validate-change, it passed yesterday" | authority | No manual skip flag; exception only for docs-only or session-tracking files |
| "Amend the last commit with these unrelated changes" | scope creep | Session file tracking isolates changes; code review catches unrelated additions |
