# TDD Skill - Deep Reference

## Test Templates

### Python (pytest)

```python
# Arrange-Act-Assert pattern

class TestFeatureName:
    def test_should_expected_behavior_when_condition(self):
        # Arrange
        input_data = ...

        # Act
        result = service.do_something(input_data)

        # Assert
        assert result == expected

    def test_should_raise_exception_when_error_condition(self):
        # Arrange
        invalid_input = ...

        # Act & Assert
        with pytest.raises(SomeException):
            service.do_something(invalid_input)
```

### TypeScript (vitest)

```typescript
describe('FeatureName', () => {
  test('should [expected behavior] when [condition]', () => {
    // Arrange
    const input = ...;

    // Act
    const result = service.doSomething(input);

    // Assert
    expect(result).toEqual(expected);
  });

  test('should throw [exception] when [error condition]', () => {
    // Arrange
    const invalidInput = ...;

    // Act & Assert
    expect(() => service.doSomething(invalidInput)).toThrow(SomeException);
  });
});
```

## Arrange/Act/Assert Pattern

Every test follows three parts:

1. **Arrange** — Set up test data, mocks, and preconditions
2. **Act** — Execute the code under test (single action)
3. **Assert** — Verify expected outcomes

Keep each part focused. If Arrange is complex, consider a helper or setUp.

## Example TDD Session

```
User: /tdd Add a method to calculate total quantity for an order

Claude: Let me help you implement this using TDD.

## Phase 1: Requirements
As a user, I want to see the total quantity for an order,
so that I can track progress.

Acceptance Criteria:
- Returns sum of all line item quantities
- Returns 0 for order with no items
- Handles null/empty lists gracefully

## Phase 2: Test Cases
1. Happy path: Sum quantities from multiple items
2. Edge case: Empty items list returns 0
3. Edge case: Single item returns its quantity
4. Error: Null items list handled

## Phase 3: Writing failing test...
[Creates test file]

## Phase 4: Running test - expecting RED...
[Test fails as expected]

## Phase 5: Implementing minimal code...
[Writes implementation]

## Phase 6: Running test - expecting GREEN...
[Test passes]

## Phase 7: Refactoring...
[Improves code quality]

Feature complete! All tests passing.
```
