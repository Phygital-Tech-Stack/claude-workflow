# Commit - Deep Reference

## Pre-Commit Agent Prompt Template

Spawn with `Agent(subagent_type: "general-purpose", model: "sonnet")` and the following prompt:

```
You are running pre-commit checks for the Phast project. Execute each step and report results.

## Step 1: Identify Changes

Run:
git status --porcelain
ls -t .claude/session-files-*.txt 2>/dev/null | head -1 | xargs cat 2>/dev/null

Cross-reference the session tracking file with git status. List files that should be staged.

## Step 2: Documentation Check

Check if any CLAUDE.md file was modified in the session. If implementation files changed but related CLAUDE.md was not updated, flag as WARNING.

Skip this step for test-only or formatting-only changes.

## Step 2.5: Lattice Gate Check (HARD GATE)

Check if /validate-change has been run this session:
- Look for recent validation output in the session
- If not run, return: GATE_BLOCKED — "/validate-change has not been run for these files"

Exception: If ALL changed files are *.md or .claude/* files, the gate passes automatically.

## Step 2.7: Task Completion Check

Check if docs/plans/3-in-progress/*-progress.md exists:
ls docs/plans/3-in-progress/*-progress.md 2>/dev/null

If found, check for unchecked steps (lines matching "- [ ]"). Warn about unchecked items.
Skip for --all flag or docs-only changes.

## Step 4: Format and Analyze

Run on session Dart files:
dart format {session_dart_files}
flutter analyze lib/ --no-fatal-infos
dart analyze phast_backend/lib/

## Output Format

PRE-COMMIT RESULTS:
- Files to stage: [list]
- Session tracking file: [path or "none"]
- Documentation drift: PASS|WARNING [details]
- Lattice gate: PASS|GATE_BLOCKED [details]
- Task completion: PASS|WARNING [unchecked items]
- Format: PASS|FIXED [details]
- Analysis (frontend): PASS|FAIL|N/A [details]
- Analysis (backend): PASS|FAIL|N/A [details]
- BLOCKING ISSUES: [list or "none"]
```

## Post-Commit Agent Prompt Template

Spawn with `Agent(subagent_type: "general-purpose", model: "sonnet")` and the following prompt:

```
You are running post-commit procedures for the Phast project. The commit hash is {commit_hash} with message "{commit_message}".

## Step 5.5: Update Progress File

Check if docs/plans/3-in-progress/*-progress.md exists for the current work.
If found:
- Move completed items from "Current" to "Completed"
- Update "Last session" date to today
- Update "Next Session Should" if work continues

## Step 5.7: Archive Completed Plans

Check if a design/progress file pair has all steps checked off (no "- [ ]" remaining, or Status: COMPLETED).
If so: move both files (*-design.md and *-progress.md) to docs/plans/4-done/

## Step 7: Write Session Progress File

Write to .claude/progress/{timestamp}-{session_id}.md:

# Session: {commit scope}
**Date**: {YYYY-MM-DD HH:MM}
**Commit**: {short hash} {full commit message}

## Files Changed
- {list each committed file from: git diff-tree --no-commit-id --name-only -r HEAD}

## What Was Done
- {1-3 bullet summary from commit message}

## Next Session Should
- {inferred follow-up tasks}

## Step 7.5: Append to Decision Log

If architectural decisions were made (check commit message for architecture keywords), append to .claude/decisions.log:

## {YYYY-MM-DD} | {commit hash} | {scope}
- {decision summary}
- Rationale: {why this approach was chosen}

## Step 8: Clean Up Tracking File

Remove committed paths from session tracking file:
committed=$(git diff-tree --no-commit-id --name-only -r HEAD)
SF=$(ls -t .claude/session-files-*.txt 2>/dev/null | head -1)
if [ -n "$SF" ] && [ -f "$SF" ]; then
  grep -vxF "$committed" "$SF" > "$SF.tmp" 2>/dev/null
  mv "$SF.tmp" "$SF"
  [ ! -s "$SF" ] && rm -f "$SF"
fi

## Output Format

POST-COMMIT RESULTS:
- Progress file updated: YES|NO|N/A [details]
- Plans archived: YES|NO [details]
- Session progress written: [path]
- Decision log updated: YES|NO
- Tracking file cleaned: YES|NO
```

## Post-Commit Checklist (Step 6)

After a successful commit, perform these in order:

1. **Update progress file** — If `docs/plans/3-in-progress/*-progress.md` exists, move completed items and update "Next Session Should"
2. **Archive completed plans** — If all steps checked off, move design + progress to `docs/plans/4-done/`
3. **Write session progress** — Save to `.claude/progress/<TIMESTAMP>-<SESSION_ID>.md`
4. **Append decisions** — If architectural decisions were made, append to `.claude/decisions.log`
5. **Clean up tracking file** — Remove committed paths from `.claude/session-files-<session_id>.txt`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `--no-verify` | Fix the lint/type error, never skip hooks |
| Pushing to main without confirming | Always confirm before pushing |
| `git add .` / `git add -A` | Stage files by name |
| Committing without /validate-change | Run /validate-change first — hard gate |
| Committing `.env` or credentials | Exclude sensitive files, warn user |
| Amending with unrelated changes | Session file tracking isolates changes; review catches drift |

## Error Handling

| Error | Action |
|-------|--------|
| **Lattice not run** | Block commit, tell user to run `/validate-change` |
| **Lint fails** | Fix issue. NEVER use `--no-verify` |
| **Secrets detected** | ABORT immediately. Do not commit under any circumstances |
| **No changes** | Inform user, stop |
| **Hook failure** | Investigate root cause. Never bypass with `--no-verify` |
| **Merge conflict in staging** | Resolve conflicts before staging. Never force-add |

## Conventional Commit Types

| Type | When to Use |
|------|------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `style` | Formatting, whitespace, linting fixes |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Maintenance, dependency updates, config changes |
| `perf` | Performance improvements |
