# Promote Candidates Review: PRs #26-32

**Date**: 2026-03-16
**Status**: Approved — ready for cherry-pick implementation

## Context

7 auto-generated PRs from drift-check CI. Each contains LOCAL-EDIT changes from project repos. Full diff review completed — changes triaged into promotable (generic) vs non-promotable (project-specific).

## Cherry-Pick List (implement these)

### 1. `base/hooks/prompt-submit.sh` — expanded dangerous patterns
**Source**: #26 (pharos-mcp)

Replace the simple list with a richer dict. Adopt the pharos-mcp version which adds:
- `drop schema`, `truncate table`
- `git push --force main/master`
- `reset --hard`
- `rm -rf ~`

Multiple descriptions per match for better UX.

### 2. `base/hooks/subagent-start.sh` — merge 3 improvements
**Sources**: #26 (pharos-mcp), #28 (phronesis), #29 (www)

Combine:
- **#28**: Sanitize `agent_name` input with `re.sub(r'[^a-zA-Z0-9_-]', '', ...)` (security: prevents path traversal)
- **#26**: Simplify auto-memory lookup to direct path construction instead of directory scanning
- **#29**: If keeping directory scan, use exact prefix match (`d == cwd_slug or d.startswith(cwd_slug + "-")`)

Recommendation: Adopt #26's approach (direct path) + #28's sanitization. This subsumes #29's fix since we no longer scan directories.

### 3. `stacks/python-fastapi/hooks/ruff_format.sh` — prefer venv binary
**Source**: #29 (www)

Look for `.venv/bin/ruff` first, fall back to global `ruff`. Correct for Python venv workflows.

### 4. `stacks/python-fastapi/hooks/mypy_check.sh` — prefer venv binary
**Source**: #29 (www)

Same pattern: `.venv/bin/mypy` first, fall back to global.

### 5. `stacks/typescript-nestjs/hooks/prettier_format.sh` — combined prettier + eslint
**Source**: #32 (phlow)

Combines format + lint in one hook. But **strip the `python3` → `py` change** — keep `python3`.

### 6. `stacks/csharp-dotnet/hooks/dotnet_analyze.sh` — format + analyze + loop fix
**Source**: #32 (phlow)

Adds `dotnet format` step before analysis. Fixes while-loop boundary (`"$DIR" != "."` guard). But **strip the `python3` → `py` change**.

### 7. `base/skills/brainstorm/SKILL.md` — add cross-reference
**Source**: #30 (PhX)

Add: `- **See also**: `/ai-guardrails-audit` for verifying design docs don't drift from guardrails`

### 8. `base/skills/security/SKILL.md` — add cross-reference
**Source**: #30 (PhX)

Add: `- **See also**: `/tdd` for writing security regression tests`

## Rejected Changes (with reasons)

| Change | PRs | Reason |
|--------|-----|--------|
| Agent descriptions hardcoded to FastAPI/Supabase/React | #28 | Project-specific |
| Skill commands: `pytest`, `dotnet test`, `pnpm nx` replacing `{{placeholders}}` | #28, #29, #30, #31 | Project-specific — master uses placeholders |
| `python3` → `py` alias in all hooks | #32 | phlow-specific, breaks all other systems |
| Extension narrowing (remove `.dart`, `.cs`) | #28, #32 | Reduces coverage for multi-stack support |
| Table formatting (181+/181- in score-guardrails) | #31 | Pure cosmetic noise |
| `model: sonnet` vs `model: opus` for security skill | #28 vs #29 | Projects disagree; master should not hardcode |
| `brainstorm/SKILL.md` principle consolidation (7→4) | #27 | Opinionated reduction, removes useful detail |

## PR Disposition

After cherry-picks are applied, close all 7 PRs with comment:
> Reviewed. Generic improvements cherry-picked into master (commit XXXX). Project-specific changes (hardcoded commands, stack references, `py` alias) rejected. Projects should `/sync-workflow --update` to pull the new baseline.

## Verification

1. `bash -n` all modified hook scripts
2. Verify no `py ` references (must be `python3`)
3. Run `git diff` to confirm only intended changes
