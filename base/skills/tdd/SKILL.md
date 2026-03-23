---
name: tdd
description: Use when implementing features or fixing bugs test-first. Enforces Red-Green-Refactor cycle with project test conventions.
user-invocable: true
argument-hint: <feature description>
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# /tdd - Test-Driven Development Workflow (Full Ceremony)

**Important**: Test-first is the DEFAULT behavior for all implementation work. Claude automatically writes failing tests before implementation code — no skill invocation needed.

Use `/tdd` when you want the **full structured ceremony**: requirements analysis, test case design, explicit RED/GREEN/REFACTOR phases with verification at each step. This is useful for complex features where upfront test design prevents rework.

## TDD Cycle

```
RED: Write failing test → GREEN: Minimal code to pass → REFACTOR: Improve while green → Repeat
```

## Workflow Phases

### Phase 1: Requirements Analysis

Based on `$ARGUMENTS`, create user stories with acceptance criteria. Ask for clarification if requirements are ambiguous.

### Phase 2: Test Case Design

Before writing any implementation code, design test cases covering:
- **Happy path** — Normal operation
- **Edge cases** — Boundary conditions, empty/null input
- **Error scenarios** — Invalid input, network failure
- **Integration** — Component interaction

### Phase 3: Write Failing Tests (RED)

**Test file convention:** test/<path>/<name>_test.dart

Run tests to confirm they fail:
```bash
flutter test && cd phast_backend && dart test
```

See `reference.md` for test template and Arrange/Act/Assert pattern.

### Phase 4: Implement Minimal Code (GREEN)

Write the minimum code to make tests pass. No gold-plating, no premature optimization, no extra features.

```bash
flutter test && cd phast_backend && dart test
```

### Phase 5: Refactor (REFACTOR)

With passing tests, improve: remove duplication, improve naming, extract methods >20 lines, simplify conditionals. Run tests after each change.

### Phase 6: Repeat

Return to Phase 3 for the next test case until all acceptance criteria are met.

### Phase 7: Final Verification

```bash
flutter test && cd phast_backend && dart test
flutter analyze lib/ --no-fatal-infos && dart analyze phast_backend/lib/
dart format
```

## TDD Checklist

- [ ] All user stories have corresponding tests
- [ ] All tests pass
- [ ] No implementation code without a test
- [ ] Code is refactored and clean
- [ ] Analysis passes with no errors
- [ ] Edge cases and error scenarios covered

## Related Skills

- **See also**: `/validate-change` after completing TDD cycle
- **See also**: `/commit` to commit the feature with tests
- **See also**: `/brainstorm` for designing complex features before TDD
- **See also**: `/validate-handler` for validating backend handlers created during TDD

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Write the feature first, we'll add tests after" | sunk cost + time | Workflow phases enforce test-first order: Phase 3 (RED) must precede Phase 4 (GREEN) |
| "This is a one-line fix, TDD is overkill" | authority | Skill applies to "fixing bugs" — even one-line fixes get a regression test |
| "The test is hard to write, just test manually" | exhaustion | Phase 2 designs test cases first; Phase 7 requires automated verification before completion |
