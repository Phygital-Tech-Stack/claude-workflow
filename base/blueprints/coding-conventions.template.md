# Coding Conventions — Deep Reference

> Single source of truth for naming, limits, patterns, and banned practices.

## Naming Conventions

### Classes & Types

<!-- PROJECT-SPECIFIC: Add your project's class naming conventions here -->
<!-- Example:
| Category | Convention | Example |
|----------|-----------|---------|
| Service | `<Domain>Service` | `UserService`, `OrderService` |
| Controller | `<Feature>Controller` | `DashboardController` |
| Repository | `<Entity>Repository` | `UserRepository` |
| Model | Domain noun, PascalCase | `User`, `Order`, `Product` |
-->

### Variables & Functions

| Category | Convention | Good | Bad |
|----------|-----------|------|-----|
| Boolean | `is<State>`, `has<Thing>`, `can<Action>` | `isLoading`, `hasPermission` | `loading`, `permission` |
| Callback | `on<Event>` | `onTap`, `onRetry`, `onSubmit` | `tapHandler`, `doRetry` |
| Private | language-standard prefix | (language-specific) | (language-specific) |

### Files

<!-- PROJECT-SPECIFIC: Add your project's file naming conventions here -->
<!-- Example:
| Category | Convention | Example |
|----------|-----------|---------|
| Component | `<feature>.<ext>` | `user-profile.tsx` |
| Test | `<source>.<test-ext>` | `user-profile.spec.ts` |
-->

## File Size Limits

| File Type | Soft Limit | Hard Limit | Action at Soft | Action at Hard |
|-----------|-----------|------------|----------------|----------------|
| Service/Logic | 300 lines | 500 lines | Review scope | Split responsibilities |
| UI Component | 400 lines | 600 lines | Plan extraction | Must extract |
| Controller | 300 lines | 450 lines | Review complexity | Split |
| Test file | 500 lines | 800 lines | Group by concern | Split test file |

<!-- PROJECT-SPECIFIC: Override with your project's limits if different -->

## Function Length

- **Target**: < 30 lines per function/method
- **Warning**: 30-50 lines — consider extraction
- **Hard limit**: > 50 lines — must extract

## Import Ordering

Imports should be grouped and ordered:

1. **Standard library** imports
2. **Third-party** package imports
3. **Project** internal imports

Separate groups with a blank line.

## Layer Boundaries

Architecture follows a top-down dependency rule: higher layers may depend on lower layers, but **never the reverse**.

| Layer (top→bottom) | May import | Must NOT import |
|--------------------|-----------|-----------------|
| Controller / Router / Screen | Service | Repository, Entity/Model directly |
| Service / Provider | Repository, Entity/Model | Controller / Router / Screen |
| Repository | Entity / Model | Service, Controller |
| Entity / Model | (none — leaf layer) | Any higher layer |

**Rationale**: Enforcing layer boundaries prevents circular dependencies, keeps business logic testable in isolation, and ensures UI/API layers don't bypass the service layer.

**Enforcement**: Stack-specific PreToolUse hooks warn when imports violate these rules. The hook is advisory (not a blocker) to allow legitimate exceptions such as shared types or DTOs that cross layers.

## Banned Patterns

| Pattern | Reason | Alternative |
|---------|--------|-------------|
| `// hack` / `// workaround` | Quick-fix markers indicate root cause not addressed | Fix the root cause |
| `// TODO: fix later` | Deferred work with no tracking | Create an issue or fix now |
| Hardcoded secrets | Security risk | Use environment variables |
| `any` type (TypeScript) | Type safety bypass | Define proper types |
| Catch-all error suppression | Hides real bugs | Handle specific errors |

<!-- PROJECT-SPECIFIC: Add your project's banned patterns here -->

## Single Responsibility

- Each file should have ONE primary responsibility
- If a file has multiple unrelated concerns, split it
- If a class name contains "And" or "Or", it probably does too much

## YAGNI (You Aren't Gonna Need It)

- Don't add abstractions for hypothetical future requirements
- Three similar lines of code are better than a premature abstraction
- If you're adding a parameter "just in case", don't
- Remove unused code rather than commenting it out

## Extraction Rules

When a file approaches its soft limit:

1. Identify logical groups of related code
2. Extract to new files with focused responsibility
3. Keep the original file as orchestrator/entry point
4. Ensure tests follow the extracted code
5. Verify no circular dependencies introduced

<!-- PROJECT-SPECIFIC: Add your project's extraction patterns and examples here -->
