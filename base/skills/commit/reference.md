# Commit - Deep Reference

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
