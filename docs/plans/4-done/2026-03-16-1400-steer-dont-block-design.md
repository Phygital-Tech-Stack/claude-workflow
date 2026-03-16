# Design: Adopt 'Steer, Don't Block' Pattern for Guardrails

**Issue:** #24
**Status:** Draft
**Date:** 2026-03-16

## Problem

The workflow has 3 blocking guards that hard-stop sessions on violations. Blocking guards cause friction in agentic workflows — a hard stop cascades into broken multi-step chains. The codebase is already ~70% advisory, but the remaining blockers create inconsistency and unnecessary interruptions.

## Decision Summary

| Decision | Choice |
|----------|--------|
| Scope | Convert `quick-fix-blocker` and `ts-ignore-blocker` to steering. Keep `check-file-size` as a blocker. |
| Escalation | Warn once, trust the agent. Downstream validation (`/validate-change`, `/commit`) catches unresolved issues. |
| Scoring | Update D6 rubric to accept steering with downstream validation as equivalent to blocking. |
| Approach | Modify guards in-place (minimal diff). ~4 files touched. |
| Severity label | `[STEER]` prefix for converted guards. |
| Documentation | New "Steering Philosophy" subsection in WORKFLOW.md under Guards. |

## Changes

### 1. Convert `quick-fix-blocker.json` (base)

**Before:**
```json
{
  "decision": "block",
  "reason": "[ROOT-CAUSE] BLOCKED: Detected {pattern}. Quick-fix markers are not allowed. Fix the root cause instead."
}
```

**After:**
```json
{
  "systemMessage": "[STEER] Detected {pattern}. Quick-fix markers suggest a workaround rather than a root-cause fix. Consider addressing the underlying issue."
}
```
- Exit code: 2 → 0
- Behavior: Hard stop → Advisory warning

### 2. Convert `ts-ignore-blocker.json` (typescript-nestjs stack)

**Before:**
```json
{
  "decision": "block",
  "reason": "[ROOT-CAUSE] BLOCKED: Fix the type error instead of suppressing it."
}
```

**After:**
```json
{
  "systemMessage": "[STEER] Type suppression detected. Fix the type error instead of suppressing it with @ts-ignore or @ts-nocheck."
}
```
- Exit code: 2 → 0
- Behavior: Hard stop → Advisory warning

### 3. Add "Steering Philosophy" section to `base/WORKFLOW.md`

New subsection after the Guards/Hooks reference:

```markdown
## Steering Philosophy

Guards default to **steer, don't block**:
- `systemMessage` with `[STEER]` prefix
- exit 0 (non-blocking)
- Downstream validation catches unresolved issues

**When to block** (exit 2, `decision: block`):
- Hard structural limits (file size)
- Changes that are expensive to reverse

**Severity labels:**
| Label | Meaning |
|-------|--------|
| [STEER] | Guidance, proceed with care |
| [GUARD] | Infrastructure alert |
| [SECURITY] | Security advisory |
| [BOUNDARY] | Architecture violation |
| [ROOT-CAUSE] BLOCKED | Hard stop (reserved) |
```

### 4. Update scoring rubric in `base/skills/score-guardrails/reference.md`

**D6 tier 2 change:**
- Before: "2-3 hooks including at least one blocker"
- After: "2-3 hooks including at least one enforcing guard (blocker or steering with downstream validation)"

## Files Touched

| File | Change |
|------|--------|
| `base/guards/quick-fix-blocker.json` | Convert block → steer |
| `stacks/typescript-nestjs/guards/ts-ignore-blocker.json` | Convert block → steer |
| `base/WORKFLOW.md` | Add Steering Philosophy section |
| `base/skills/score-guardrails/reference.md` | Update D6 tier 2 wording |

## What Stays the Same

- `check-file-size.json` remains a blocker (hard structural limit)
- All existing steering guards unchanged
- All lifecycle hooks unchanged (already advisory)
- Settings wiring unchanged (no guard renames)

## Risks

| Risk | Mitigation |
|------|-----------|
| Agent ignores [STEER] warnings and ships hack code | `/validate-change` lattice and `/commit` pre-commit checks catch violations downstream |
| Score drops for projects using this pattern | D6 rubric updated to accept steering as equivalent enforcement |
| Naming confusion (`*-blocker` files that don't block) | Acceptable trade-off vs. file rename churn; names reflect original intent |

## Test Plan

- [ ] Trigger `quick-fix-blocker` with `// hack` comment — verify systemMessage instead of block
- [ ] Trigger `ts-ignore-blocker` with `@ts-ignore` — verify systemMessage instead of block
- [ ] Trigger `check-file-size` with oversized file — verify still blocks
- [ ] Run `/score-guardrails` — verify D6 score unchanged
- [ ] Verify WORKFLOW.md renders correctly with new section
