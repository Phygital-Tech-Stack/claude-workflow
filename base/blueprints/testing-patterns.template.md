# Testing Patterns — Deep Reference

> Deep reference for test organization, patterns, mocks, and fixtures. Companion to the `/tdd` skill.

## Test Organization

### Where Tests Live

<!-- PROJECT-SPECIFIC: Add your project's test directory structure here -->
<!-- Example:
| Component | Test Location | Runner |
|-----------|--------------|--------|
| Backend | `tests/` | `pytest` |
| Frontend | `src/__tests__/` | `jest` |
-->

### File Naming

Test files mirror source files with a test suffix:

```
{{TEST_FILE_CONVENTION}}
```

<!-- PROJECT-SPECIFIC: Add your project's test file naming examples here -->

## TDD Cycle

```
RED: Write a failing test that describes the desired behavior
GREEN: Write the minimum code to make the test pass
REFACTOR: Improve the code while keeping tests green
```

### When to Use TDD

| Scenario | TDD Approach |
|----------|-------------|
| New feature | Start with acceptance criteria → test cases → implementation |
| Bug fix | Write a test that reproduces the bug → fix → verify |
| Refactoring | Ensure existing tests pass → refactor → verify |
| API endpoint | Define contract → test request/response → implement |

## Test Quality Standards

### Arrange-Act-Assert (AAA)

Every test follows three parts:

```
// Arrange — Set up test data, mocks, and preconditions
// Act — Execute the code under test (single action)
// Assert — Verify expected outcomes
```

### Test Naming

Tests should clearly describe:
- **What** is being tested (unit/function name)
- **When** (the condition/scenario)
- **Then** (the expected outcome)

Pattern: `should [expected behavior] when [condition]`

### Coverage Categories

For each feature, ensure tests cover:

| Category | Examples |
|----------|---------|
| **Happy path** | Normal operation with valid inputs |
| **Edge cases** | Empty/null input, boundary values, max/min |
| **Error handling** | Invalid input, network failure, timeout |
| **Integration** | Component interaction, API contracts |

## Mock Patterns

### When to Mock

| Mock | Don't Mock |
|------|-----------|
| External APIs / network calls | Simple data transformations |
| Database queries | Pure functions |
| File system operations | Value objects |
| Time-dependent operations | Domain logic |
| Third-party services | Internal utilities (usually) |

### Mock Guidelines

- Mock at boundaries, not within the unit under test
- Prefer stubs (return values) over spies (verify calls) when possible
- Keep mock setup close to the test that uses it
- Reset mocks between tests

<!-- PROJECT-SPECIFIC: Add your framework-specific mock patterns here -->
<!-- Example for Jest:
```typescript
jest.mock('../services/user-service');
const mockUserService = jest.mocked(UserService);
mockUserService.findById.mockResolvedValue(testUser);
```
-->

## Test Data

### Fixtures vs Inline Data

| Use Fixtures When | Use Inline Data When |
|-------------------|---------------------|
| Same data across multiple tests | Data is specific to one test |
| Complex object construction | Simple values (strings, numbers) |
| Shared between test files | Clarity improves with inline |

### Test Data Guidelines

- Use descriptive values (`"test-user@example.com"` not `"a@b.c"`)
- Avoid magic numbers — use named constants
- Don't share mutable state between tests
- Clean up test data after each test (or use isolated setup)

## Per-Layer Test Patterns

<!-- PROJECT-SPECIFIC: Add your project's layer-specific test patterns here -->
<!-- Example sections:
### Unit Tests (Services/Logic)
### Integration Tests (API/Database)
### Component Tests (UI)
### End-to-End Tests
-->

## Common Testing Mistakes

| Mistake | Fix |
|---------|-----|
| Testing implementation details | Test behavior and outcomes, not internal methods |
| Brittle assertions on exact strings | Use pattern matching or key field checks |
| Tests that depend on execution order | Each test should be independent |
| Slow tests in the main suite | Move integration tests to separate suite |
| No test for the bug fix | Every bug fix gets a regression test |
| Testing framework code | Trust the framework; test YOUR logic |

## Continuous Testing

```bash
# Run tests for changed files only
{{TEST_COMMAND}}

# Watch mode (re-run on file change)
{{WATCH_COMMAND}}
```
