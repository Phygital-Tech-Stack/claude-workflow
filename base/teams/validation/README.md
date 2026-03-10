# Validation Team

Team prompts for parallelized code review. Used by `/validate-change --team`.

## Prompt Inventory

| Prompt                 | Role                    | Model | Purpose                                                    |
| ---------------------- | ----------------------- | ----- | ---------------------------------------------------------- |
| `security-reviewer.md` | Security specialist     | Opus  | Runs security checks (secrets, deps, auth) + triages       |
| `code-reviewer.md`     | Code quality reviewer   | Opus  | Reviews against coding standards, auto-fixes safe issues   |
| `arch-checker.md`      | Architecture compliance | Opus  | Checks module boundaries, complexity, dead code            |

## Usage

Invoked automatically by `/validate-change --team` (default mode). Each teammate runs as a parallel Task and produces a severity-tiered report. The lead aggregates results:

- **Overall FAIL** if any teammate reports a BLOCK finding
- **Overall WARN** if any WARN findings (no BLOCK)
- **Overall PASS** if all teammates PASS

## Cross-Cutting Refactor Pattern

For large refactors that apply the same change across multiple modules (e.g., "add field to all tables", "migrate all repositories to new pattern", "add dark mode to all pages"):

### Steps

1. **Define the change pattern** -- Lead describes exactly what to change per module, with before/after examples
2. **List affected modules** -- Lead inventories all files that need the change (use `Grep`/`Glob`)
3. **Spawn one teammate per module** -- Each teammate receives the pattern definition + its assigned module files
4. **Each teammate applies the pattern** -- Modifies owned files, runs module-scoped tests
5. **Lead reviews consistency** -- Verifies all teammates applied the same pattern, fixes any drift
6. **Lead runs `/validate-change --team`** -- Full validation lattice on the combined changeset

### Teammate Spawn Template

```
Use Task tool with subagent_type="general-purpose", model="sonnet":

Prompt:
  You are refactoring the {module} module.

  CHANGE PATTERN:
  {description of what to change, with before/after code examples}

  YOUR FILES:
  {list of files this teammate owns}

  RULES:
  - Apply the pattern exactly as shown
  - Run tests for your module: {{TEST_COMMAND}}
  - Report: files changed, tests passed/failed, any deviations from pattern

  DO NOT touch files outside your assigned module.
```

### When to Use This Pattern

- Same structural change needed in 3+ modules
- Each module's changes are independent (no cross-module dependencies in the refactor)
- The change is mechanical enough to describe as a pattern with before/after examples

### When NOT to Use This Pattern

- Changes that require cross-module coordination (use sequential mode)
- Fewer than 3 modules affected (just do it sequentially)
- Exploratory refactors where the pattern isn't clear yet (use `/brainstorm` first)
