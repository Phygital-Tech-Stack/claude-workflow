# Validate Change - Deep Reference

## Layer 1: Deterministic — Full Commands

### Format Check

```bash
# Check formatting on changed files (non-destructive)
{{FORMAT_COMMAND}} --check <changed_files>

# Auto-fix formatting (if check fails)
{{FORMAT_COMMAND}} <changed_files>
```

### Static Analysis

```bash
# Run analysis on changed directories
{{ANALYZE_COMMAND}}
```

## Layer 2: Semantic — Full Commands

### Tests

```bash
# Run tests
{{TEST_COMMAND}}
```

### Cross-Boundary Impact Trace

When shared files change, identify all consumers and verify they still compile/pass.

**Trace rules** (project-specific — define in stack `commands.yaml`):
- Shared library changed → rebuild all consumers
- Schema/migration changed → verify generated code is current
- Config changed → verify all components still start

### Visual Verification (flutter-dart only)

When UI files (widgets, screens, pages) are changed in a flutter-dart stack:
1. Take a screenshot: `{{SCREENSHOT_COMMAND}}`
2. Compare against baseline in `docs/screenshots/` if available
3. Flag visual regressions for human review (Layer 5)

**Convention**: Baseline screenshots live in `docs/screenshots/`, named after the screen/component. Updated by developers after intentional design changes, not by Claude automatically.

## Layer 3: Security — Full Commands

### Secret Scanning

```bash
# Run gitleaks with project config
gitleaks detect --no-git -c .gitleaks.toml --source . 2>&1
```

### File Size Check

Check changed files against project-specific thresholds defined in stack config.

### Dependency Check

```bash
# Check for outdated dependencies (advisory, not blocking)
# Command is stack-specific
```

## Layer 4: Agentic — Invocation

Invoke the `code-reviewer` agent:

```
Task tool with subagent_type="code-reviewer"
Prompt: "Review these changed files for pattern adherence and quality: [file list].
Classify each finding as BLOCK, WARN, or INFO."
```

### Severity Tiers

#### BLOCK Tier (Verdict = FAIL — must fix before commit)

- Architecture boundary violations
- File exceeds hard size limit
- Missing error handling on critical paths
- Security vulnerabilities
- Deprecated patterns in use

#### WARN Tier (Verdict = WARN — escalate to Layer 5)

- File approaching soft size limit
- Functions/methods > 50 lines
- Generic naming (`data`, `handleChange`, `doStuff`)
- Missing test coverage for changed behavior

#### INFO Tier (No verdict impact — advisory)

- Import ordering issues (auto-fixed by hooks)
- Formatting inconsistencies (auto-fixed by hooks)
- Over-documentation (comments restating code)

### Escalation

BLOCK-tier findings stop the pipeline (FAIL verdict). WARN-tier findings escalate to Layer 5 for human decision. INFO-tier findings are resolved silently.

## Layer 5: Human — Escalation Format

```markdown
## Escalations Requiring Decision

### BLOCK Findings (Must Fix)

1. **[BLOCK]** `file:line` — Description
   - **Category**: Architecture / Complexity / etc.
   - **Fix**: Specific remediation

### WARN Findings (Decide: Fix or Override)

1. **[WARN]** `file:line` — Description
   - **Category**: Complexity / Naming / etc.
   - **Recommendation**: Suggested fix

### Options

a) **Fix and re-validate** — Address the issues, run `/validate-change` again
b) **Override WARN findings with reason** — Document why acceptable, proceed to `/commit`
c) **Abort** — Stop and rethink the approach

Note: BLOCK findings cannot be overridden. They must be fixed.
```

## Auto-Quick Detection

Quick mode is **auto-detected**, not user-selected.

### Auto-Quick Criteria (ALL must be true)

- Changed files are ONLY: {{AUTO_QUICK_PATTERNS}}
- No files in critical source directories
- Fewer than 3 files changed
- No new files created

### When Auto-Quick Activates

Run Layers 1-2 only. Note in verdict: `(auto-quick: docs/test-only change)`.

## Example Output — Full Pass

```
## Validation Result: PASS

| Layer | Check | Result | Detail |
|-------|-------|--------|--------|
| 1-Deterministic | Format | PASS | Clean |
| 1-Deterministic | Analysis | PASS | No issues |
| 2-Semantic | Tests | PASS | N passed, 0 failed |
| 2-Semantic | Cross-boundary | N/A | No shared changes |
| 3-Security | Secrets | PASS | No patterns found |
| 3-Security | File Sizes | PASS | All under limits |
| 4-Agentic | Code Review | PASS | 0 BLOCK, 0 WARN |

Ready for /commit.
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Layer 1 format check fails | Formatter not run | Run format command then re-run |
| Layer 1 analysis hangs | Large codebase scan | Scope to changed directories only |
| Layer 2 tests timeout | Long-running tests | Use timeout flag or run specific tests |
| Layer 3 gitleaks not found | gitleaks not installed | Install gitleaks |
| Layer 4 agent slow | Large diff | Review is proportional to change size |
| "No changes" but files modified | Unstaged changes | Check `git status` |
