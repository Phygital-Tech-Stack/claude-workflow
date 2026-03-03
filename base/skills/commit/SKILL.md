---
name: commit
description: Use when committing code changes after a work session.
user-invocable: true
argument-hint: [--all | --amend]
allowed-tools: Bash, Read, Grep, Glob, Edit, Task
model: opus
---

# Smart Commit Command

**PURPOSE**: Create quality commits with session-scoped staging, lattice-gated validation, and conventional commit formatting.

## File Tracking (Compression-Proof)

A PostToolUse hook logs every file path touched by Write/Edit to `.claude/session-files-<session_id>.txt`. Use `--all` to stage everything instead.

## Steps

### 1. Identify Changes

```bash
git status --porcelain
ls -t .claude/session-files-*.txt 2>/dev/null | head -1 | xargs cat 2>/dev/null
```

Cross-reference tracking file with `git status`. Show filtered list: "These N files were tracked. Stage all?" Fallback to all changed files if tracking is empty.

### 2. Documentation Check

Invoke `/ai-guardrails-audit` in diff mode. Auto-skip for test-only or formatting-only changes.

### 2.5. Lattice Check (HARD GATE)

If `/validate-change` hasn't run this session, **block the commit**:

```
[BLOCK] /validate-change has not been run for these files. Run it first.
```

**Exception**: Docs-only changes (`*.md`) or session-tracking files (`.claude/*`).

### 2.7. Task Completion Check

If a progress file exists (`docs/plans/3-in-progress/*-progress.md`), warn about unchecked steps. Skip for `--all` or docs-only.

### 3. Code Review

Use `code-reviewer` subagent. Skip if `/validate-change` already ran this session (Layer 4 covers it).

### 4. Format and Analyze

```bash
{{FORMAT_COMMAND}}
{{ANALYZE_COMMAND}}
```

### 5. Stage and Commit

Generate conventional commit with `Co-Authored-By` trailer. **Types**: feat, fix, refactor, style, test, docs, chore, perf.

### 6. Post-Commit

Update progress files, archive completed plans, write session progress, append decisions. See `reference.md` for full post-commit checklist.

### 7. Verify

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
