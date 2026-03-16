# Plan Lifecycle

Authoritative reference for the `docs/plans/` stage system. Design docs and their companion progress files travel together through these stages.

## Stages

| Stage | Folder | Purpose | Entry Trigger |
|-------|--------|---------|---------------|
| Draft | `1-draft/` | Design in progress, not yet approved | `/brainstorm` Phase 5 |
| Approved | `2-approved/` | Approved, parked for later implementation | `/brainstorm` Phase 6 Path B |
| In Progress | `3-in-progress/` | Active implementation underway | Phase 6 Path A, or Plan Mode resume |
| Done | `4-done/` | Completed plans | `/commit` (all steps checked off) |
| Archive | `5-archive/` | Abandoned plans | Manual |

## Flow

```
    /brainstorm creates
           |
      +----v----+
      | 1-draft  |
      +----+-----+
           |
     +-----+------+
     | Phase 6    |
     v            v
  Path A       Path B
  (implement)  (park)
     |            |
     |       +----v------+
     |       | 2-approved |
     |       +----+-------+
     |            | Plan Mode
     |            | resume
     v            v
  +------------------+
  |  3-in-progress   | <-- hooks read here
  +--------+---------+
           |
     +-----+------+
     v            v
  +------+   +---------+
  |4-done|   |5-archive|
  +------+   +---------+
  /commit     manual
  (complete)  (abandon)
```

## File Naming

- Design: `YYYY-MM-DD-HHmm-<topic>-design.md`
- Progress: `YYYY-MM-DD-HHmm-<topic>-progress.md`

Both files travel together through all stages.

## Transition Triggers

| Transition | Trigger | Skill |
|------------|---------|-------|
| --> `1-draft/` | Design doc saved | `/brainstorm` Phase 5 |
| `1-draft/` --> `3-in-progress/` | User picks "Implement now" | `/brainstorm` Phase 6 Path A |
| `1-draft/` --> `2-approved/` | User picks "Park for later" | `/brainstorm` Phase 6 Path B |
| `2-approved/` --> `3-in-progress/` | Resume parked plan in Plan Mode | Plan Mode entry |
| `3-in-progress/` --> `4-done/` | All progress steps checked off | `/commit` post-commit checklist |
| `3-in-progress/` --> `5-archive/` | Plan abandoned | Manual |

## Hooks That Read Plans

| Hook | Reads From | Purpose |
|------|-----------|---------|
| `session-start.sh` | `3-in-progress/*-progress.md` | Extract "Next Session Should" items |
| `teammate-idle.sh` | `3-in-progress/*-progress.md` | Check for unchecked steps on idle plans |
