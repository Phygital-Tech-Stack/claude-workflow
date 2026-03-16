# Design: Document docs/plans/ Lifecycle

**Issue:** #25
**Status:** Draft
**Date:** 2026-03-16

## Problem Statement

The `docs/plans/` folder structure is partially implied across multiple files (WORKFLOW.md, brainstorm/reference.md, commit/reference.md, hooks) but never explicitly documented as a complete lifecycle. Only `1-draft/` and `4-archive/` exist on disk. Hooks read from `3-in-progress/` (doesn't exist), `/commit` references `5-archive/` (doesn't exist), and `2-approved/` is purely conceptual.

A developer following the workflow cannot answer: What stages exist? When does a file move between stages? Who triggers transitions?

## Decision Summary

| Decision | Choice |
|----------|--------|
| Scope | Full: LIFECYCLE.md + folders + skill wiring + automation |
| Archive split | Split current `4-archive/` into `4-done/` (completed) and `5-archive/` (abandoned) |
| Automation | Wire transitions directly into skills (no helper script) |
| Path A flow | Skip `2-approved/` for immediate implementation (1-draft -> 3-in-progress) |

## Design

### Folder Structure

```
docs/plans/
├── LIFECYCLE.md       ← NEW: authoritative lifecycle reference
├── 1-draft/           ← /brainstorm Phase 5 creates files here
├── 2-approved/        ← NEW: parked designs awaiting implementation
├── 3-in-progress/     ← NEW: active implementation (hooks read here)
├── 4-done/            ← NEW: completed plans (replaces 4-archive/)
└── 5-archive/         ← NEW: abandoned plans
```

### Transition Map

| From | To | Trigger | Skill |
|------|-----|---------|-------|
| — | `1-draft/` | Design saved | `/brainstorm` Phase 5 |
| `1-draft/` | `3-in-progress/` | User picks "Implement now" | `/brainstorm` Phase 6 Path A |
| `1-draft/` | `2-approved/` | User picks "Park for later" | `/brainstorm` Phase 6 Path B |
| `2-approved/` | `3-in-progress/` | Resume parked plan in Plan Mode | Plan Mode entry |
| `3-in-progress/` | `4-done/` | All progress steps checked off | `/commit` post-commit |
| `3-in-progress/` | `5-archive/` | Plan abandoned | Manual |

### Skill Changes

#### `/brainstorm` reference.md — Phase 6

**Path A (Implement now):**
1. Move design + progress files: `1-draft/` -> `3-in-progress/`
2. Update progress file Status: `NOT STARTED` -> `IN PROGRESS`
3. Enter Plan Mode with design doc as context

**Path B (Park for later):**
1. Move design + progress files: `1-draft/` -> `2-approved/`
2. Update progress file Status: `NOT STARTED` -> `APPROVED`
3. Inform user: "Design parked in `2-approved/`. Start a new session and enter Plan Mode to begin."

#### `/commit` reference.md — Post-Commit Checklist

Update steps 1-2:
1. **Update progress file** — If `docs/plans/3-in-progress/*-progress.md` exists, move completed items and update "Next Session Should"
2. **Archive completed plans** — If all steps checked off, move design + progress to `docs/plans/4-done/`

#### `WORKFLOW.md` — New Feature workflow

Update Steps 1-2 to show stage transitions:

```
Step 1: /brainstorm <feature>
        └── Saves design doc to docs/plans/1-draft/ (Phase 5)

Step 2: Approve design (end of /brainstorm Phase 6)
        ├── Path A: Implement now → files move 1-draft/ → 3-in-progress/
        └── Path B: Park → files move 1-draft/ → 2-approved/

Step 3: Plan Mode (EnterPlanMode)  [if Path B, start here next session]
        └── If resuming from 2-approved/, move to 3-in-progress/ first
```

Update Reference section:
- Add: `Approved plans: docs/plans/2-approved/*-design.md`
- Change: `Archived plans: docs/plans/4-done/` and `docs/plans/5-archive/`

### LIFECYCLE.md Content

Single authoritative doc covering:
- Stage table (folder, purpose, entry trigger)
- ASCII flow diagram showing both paths
- File naming convention (`YYYY-MM-DD-HHmm-<topic>-{design,progress}.md`)
- Transition trigger table (who/what moves files)
- Hooks that read plans (`session-start.sh`, `teammate-idle.sh`)

## File Structure & Sizing

| File | Purpose | Estimated Lines | New/Modified |
|------|---------|----------------|--------------|
| `docs/plans/LIFECYCLE.md` | Authoritative lifecycle reference | ~80 | New |
| `docs/plans/2-approved/.gitkeep` | Stage folder | 0 | New |
| `docs/plans/3-in-progress/.gitkeep` | Stage folder | 0 | New |
| `docs/plans/4-done/.gitkeep` | Stage folder | 0 | New |
| `docs/plans/5-archive/.gitkeep` | Stage folder | 0 | New |
| `base/skills/brainstorm/reference.md` | Phase 6 transition wiring | ~10 lines changed | Modified |
| `base/skills/commit/reference.md` | Post-commit step 2 update | ~2 lines changed | Modified |
| `base/WORKFLOW.md` | New Feature steps + Reference section | ~15 lines changed | Modified |

### Reuse Assessment

- [x] No new dependencies or helpers needed
- [x] Skill-embedded `mv` commands — no abstraction layer
- [x] Hooks already read from `3-in-progress/` — no hook changes needed
- [x] No file will exceed soft size limit

## Migration

- Move existing `4-archive/` contents to `4-done/` (3 files: teams-design, guardrail-remediation-design, guardrail-remediation-progress)
- Remove empty `4-archive/` folder
- Current `1-draft/` file (steer-dont-block-design.md) stays as-is

## Alternatives Considered

1. **Centralized plan-move helper script** — Rejected: adds a new moving part for simple `mv` operations. Skills handle their own transitions.
2. **Traverse all stages for Path A** — Rejected: `2-approved/` is unnecessary when implementing immediately. Simpler to go `1-draft/` -> `3-in-progress/` directly.
3. **Keep `4-archive/` unsplit** — Rejected: distinguishing completed vs abandoned plans is valuable for audit trail.

## Risks

| Risk | Mitigation |
|------|-----------|
| Naming confusion (`4-archive/` references in git history) | One-time migration; no backward-compat needed for plan folders |
| Skills forget to `mv` files | Documented in reference.md as explicit steps; easy to verify |
| Parked plans in `2-approved/` get forgotten | `teammate-idle` hook could be extended (future issue) |

## Implementation Order

1. Create stage folders with `.gitkeep` files
2. Write `docs/plans/LIFECYCLE.md`
3. Migrate `4-archive/` -> `4-done/`
4. Update `base/skills/brainstorm/reference.md` (Phase 6)
5. Update `base/skills/commit/reference.md` (post-commit steps)
6. Update `base/WORKFLOW.md` (New Feature steps + Reference)

## Test Plan

- [ ] Verify all 5 stage folders exist with `.gitkeep`
- [ ] Verify `LIFECYCLE.md` renders correctly
- [ ] Verify `4-archive/` contents migrated to `4-done/`
- [ ] Verify `brainstorm/reference.md` Phase 6 has both Path A and Path B with `mv` instructions
- [ ] Verify `commit/reference.md` references `4-done/` (not `5-archive/`)
- [ ] Verify `WORKFLOW.md` New Feature steps show stage transitions
- [ ] Verify `WORKFLOW.md` Reference section lists all plan folders
- [ ] Run `/score-guardrails` — verify no score regression
