# Brainstorm Skill - Deep Reference

## Phase 2: Understanding the Idea

Goal: Understand the _why_ before the _what_.

Ask questions one at a time, in this order:

1. **Purpose**: "What problem does this solve?" or "What should a user be able to do that they can't today?"
2. **Scope**: "Is this for [specific context] or should it work across [broader context]?"
3. **Constraints**: "Are there any hard requirements — compatibility, performance, timeline?"
4. **Success criteria**: "How will we know this works correctly?"

## Phase 3: Exploring Approaches

Goal: Prevent premature commitment by showing real alternatives.

For each approach, provide:

```markdown
### Option A: [Name] (Recommended)

**How it works**: [2-3 sentences]
**Fits existing patterns**: [Which project patterns it aligns with]
**Trade-offs**: [Honest pros and cons]
**Effort**: [Relative: small/medium/large]
**Files touched**: [Key files that would change]

### Option B: [Name]

**How it works**: [2-3 sentences]
**Fits existing patterns**: [Which project patterns it aligns with]
**Trade-offs**: [Honest pros and cons]
**Effort**: [Relative: small/medium/large]
**Files touched**: [Key files that would change]
```

**Rules**:

- Lead with your recommended option and explain why
- Always present at least 2 options (even if one is clearly better — explain why)
- Include effort estimates relative to each other
- List actual files from the codebase that would change
- If an option requires new dependencies, say so explicitly

## Phase 4: Presenting the Design

Goal: Walk through the chosen approach in validated sections.

Break the design into **200-300 word sections**, one per message. After each section, ask:
"Does this match what you had in mind, or should we adjust?"

**Section order** (skip sections that don't apply):

1. **Architecture Overview** — Where this fits in the codebase, data flow diagram
2. **Data Model** — Schema changes, new models, field mapping
3. **Backend Design** — API endpoints, services, data access
4. **Frontend Design** — UI components, state management
5. **Integration Points** — External systems, existing services
6. **Error Handling** — What can go wrong and how to handle it
7. **Testing Strategy** — What tests to write, test data needed

### Validation Checkpoints

After each section, use AskUserQuestion:
```
[AskUserQuestion with options:
  - Looks good, continue to next section
  - I'd like to adjust something in this section
  - Let's revisit an earlier decision]
```

## Phase 5: Design Documentation

After all sections are validated, save the design:

```bash
mkdir -p docs/plans/1-draft
```

**File**: `docs/plans/1-draft/YYYY-MM-DD-HHmm-<topic>-design.md`

**Template**:

```markdown
# Design: [Feature Name]

**Date**: YYYY-MM-DD HH:mm
**Status**: Approved
**Author**: [User] + Claude

## Problem Statement

[What problem this solves]

## Decision

[Chosen approach and why]

## Design

### Architecture

[Overview and data flow]

### Data Model

[Schema changes, models]

### Backend

[API endpoints, services]

### Frontend

[UI components, state]

### Integration

[How it connects to existing systems]

## File Structure & Sizing

| File | Purpose | Estimated Lines | New/Modified |
|------|---------|----------------|--------------|
| (fill in) | | | |

### Reuse Assessment

- [ ] Checked existing services for overlapping logic
- [ ] Checked existing components for similar patterns
- [ ] Identified components that should be shared from day one
- [ ] Verified no file will exceed its soft size limit

## Alternatives Considered

[Other approaches and why they were rejected]

## Testing Plan

[What tests to write]

## Implementation Order

[Suggested sequence of PRs/commits]

## Risks

[What could go wrong]
```

Create an empty progress file alongside the design doc:

**File**: `docs/plans/1-draft/YYYY-MM-DD-HHmm-<topic>-progress.md`

```markdown
# Progress: [Feature Name]

**Design**: docs/plans/1-draft/YYYY-MM-DD-HHmm-<topic>-design.md
**Status**: NOT STARTED
**Last session**: YYYY-MM-DD

## Completed

(nothing yet)

## Current

(nothing yet)

## Blocked

(nothing)

## Next Session Should

1. Enter plan mode with design doc as context
2. Implement step 1 from the design's Implementation Order
3. Run /validate-change after implementation
```

## Phase 6: Handoff to Implementation

See `docs/plans/LIFECYCLE.md` for the full stage system.

**Path A: Implement now → Enter Plan Mode**

1. Move design + progress files from `docs/plans/1-draft/` to `docs/plans/3-in-progress/`
2. Update progress file: set `**Status**:` to `IN PROGRESS`, update `**Design**:` path
3. Confirm readiness
4. Enter Claude Code's native plan mode (EnterPlanMode) with the design doc as context
5. Do NOT re-explore approaches or re-validate the design

**Path B: Park for later**

1. Move design + progress files from `docs/plans/1-draft/` to `docs/plans/2-approved/`
2. Update progress file: set `**Status**:` to `APPROVED`, update `**Design**:` path
3. Inform user: "Design parked in `docs/plans/2-approved/`. Start a new session and enter Plan Mode to begin."

**Resuming a parked plan**

When entering Plan Mode with a design doc from `docs/plans/2-approved/`:
1. Move design + progress files from `docs/plans/2-approved/` to `docs/plans/3-in-progress/`
2. Update progress file: set `**Status**:` to `IN PROGRESS`, update `**Design**:` path

## Relationship with Plan Mode

`/brainstorm` and plan mode are **sequential, not competing**:

```
/brainstorm                          Plan Mode
-----                                -----
WHAT and WHY                         HOW and WHERE
-----                                -----
"Should we build X or Y?"           "Which files change for X?"
"What are the trade-offs?"          "What's the implementation order?"
"What constraints matter?"          "What does the code diff look like?"
-----                                -----
Output: Design document              Output: Implementation plan
```

## Anti-Patterns

- Don't write code during the brainstorm — design first, implement after
- Don't skip recon — always read the codebase before making assumptions
- Don't present only one option — there's always an alternative worth considering
- Don't design for hypothetical future requirements — solve today's problem
- Don't add complexity "just in case" — start simple, evolve when needed
- Don't ignore existing patterns — follow established project conventions
