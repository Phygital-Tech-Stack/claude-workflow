# Validate Change - Deep Reference

## Layer 1: Deterministic — Full Commands

### Format Check

```bash
# Check formatting on changed files (non-destructive)
dart format --check <changed_files>

# Auto-fix formatting (if check fails)
dart format <changed_files>
```

### Static Analysis

```bash
# Run analysis on changed directories
flutter analyze lib/ --no-fatal-infos && dart analyze phast_backend/lib/
```

## Layer 2: Semantic — Full Commands

### Tests

```bash
# Run tests
flutter test && cd phast_backend && dart test
```

### Cross-Boundary Impact Trace

When shared files change, identify all consumers and verify they still compile/pass.

**Trace rules** (project-specific — define in stack `commands.yaml`):
- Shared library changed → rebuild all consumers
- Schema/migration changed → verify generated code is current
- Config changed → verify all components still start

### Visual Verification (flutter-dart only)

When UI files (widgets, screens, pages) are changed in a flutter-dart stack:
1. Take a screenshot: `flutter screenshot --type=device --out=docs/screenshots/`
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

### Team Mode (default, `--team`)

Read `.claude/teams/validation/team.yaml` to discover the team roster. For each member:

1. Read the teammate's prompt from `.claude/teams/validation/prompts/<name>.md`
2. Spawn a parallel Task with the prompt + changed file list
3. Wait for all teammates to complete

```
# Spawn 3 parallel Tasks:
Task(code-reviewer):   "Review changed files: [file list]. <prompt from prompts/code-reviewer.md>"
Task(security-reviewer): "Review changed files: [file list]. <prompt from prompts/security-reviewer.md>"
Task(arch-checker):    "Review changed files: [file list]. <prompt from prompts/arch-checker.md>"
```

**Aggregation**: Overall verdict = worst individual verdict across all teammates.
- Any teammate returns FAIL -> overall FAIL
- Any teammate returns WARN (no FAIL) -> overall WARN
- All teammates PASS -> overall PASS

### Single-Agent Mode (`--no-team`)

Fall back to a single code-reviewer agent:

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

- Changed files are ONLY: *_test.dart, *.md, *.json
- No files in critical source directories
- Fewer than 3 files changed
- No new files created

### When Auto-Quick Activates

Run Layers 1-2 only. Note in verdict: `(auto-quick: docs/test-only change)`.

## Verdict Template

```
## Validation Result: [PASS | FAIL | WARN]

| Layer | Check | Result | Detail |
|-------|-------|--------|--------|
| 1 | Format / Analysis | PASS/FAIL | ... |
| 2 | Tests / Cross-boundary | PASS/FAIL | ... |
| 3 | Secrets / Deprecated / File Sizes | PASS/FAIL | ... |
| 4 | Code Review | PASS/WARN/FAIL | N BLOCK, M WARN |
```

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

## Delegation Pattern

### L1-L3 Agent Prompt Template

Spawn with `Agent(subagent_type: "general-purpose", model: "sonnet")` and the following prompt:

```
You are running validation layers L1-L3 for the Phast project. Execute each layer in order. Stop on first FAIL.

## Changed Files
{changed_file_list}

## Classification
{frontend|backend|packages|tests|config|docs}

## Layer 1: Deterministic

### 1a. Format Check
Run: dart format --set-exit-if-changed {changed_dart_files}
If FAIL: run `dart format {changed_dart_files}` to auto-fix, then re-check.

### 1b. Static Analysis
If frontend changed: flutter analyze lib/ --no-fatal-infos
If backend changed: dart analyze phast_backend/lib/
If packages changed: dart analyze packages/{package_name}/

### 1c. Build Runner
If any file matches (tables.dart, *.drift): run `dart run build_runner build --delete-conflicting-outputs`

## Layer 2: Semantic

### 2a. Tests
If frontend changed: flutter test --no-pub
If backend changed: (cd phast_backend && dart test)
If packages changed: (cd packages/{package_name} && dart test)

### 2b. TDD Coverage Check
For each changed implementation file (lib/, phast_backend/lib/, packages/*/lib/):
- Exclude generated files (*.g.dart, *.freezed.dart, *.drift.dart)
- Exclude entry points (main.dart, server.dart), route files, barrel files
- Map: lib/foo/bar.dart → test/foo/bar_test.dart
- Map: phast_backend/lib/x.dart → phast_backend/test/x_test.dart
- Map: packages/pkg/lib/src/x.dart → packages/pkg/test/src/x_test.dart
Severity:
- New impl file, no test file exists → BLOCK
- Existing impl changed, test not changed → WARN

### 2c. Cross-Boundary Trace
If packages/ changed, verify consumers rebuild:
- phast_models → flutter analyze lib/ + dart analyze phast_backend/lib/ + flutter analyze phast_admin/lib/
- phast_api_client → flutter analyze lib/ + flutter analyze phast_admin/lib/
- phast_utils → dart analyze phast_backend/lib/
- phast_auth → flutter analyze lib/ + flutter analyze phast_admin/lib/

## Layer 3: Security

### 3a. Secret Scanning
Run: gitleaks detect --no-git -c .gitleaks.toml --source . 2>&1

### 3b. Deprecated Pattern Scan
Search changed files for:
| Pattern | Replacement | Severity |
|---------|-------------|----------|
| withOpacity( | withValues(alpha: | FAIL |
| SysproApiClient | UnifiedSysproClient | FAIL |
| EmployeeAuthService | EmployeeAuthFacade | FAIL |
| SyncService | BackgroundTaskService | FAIL |
| SysproConfig | BackendConfig | FAIL |
| SmartModeService | ConnectivityService | FAIL |
| ApiService | Specialized clients | WARN |

### 3c. File Size Check
Thresholds:
| File Type | OK | WARN | FAIL |
|-----------|-----|------|------|
| *_screen.dart | < 800 | 800-1000 | > 1000 |
| *_handlers.dart | < 500 | 500-700 | > 700 |
| *_widget.dart | < 400 | 400-600 | > 600 |
| Controller | < 400 | 400-600 | > 600 |

## Output Format

Return results as structured text:

LAYER 1 RESULTS:
- Format: PASS|FAIL [details]
- Analysis (frontend): PASS|FAIL|N/A [details]
- Analysis (backend): PASS|FAIL|N/A [details]
- Analysis (packages): PASS|FAIL|N/A [details]
- Build Runner: PASS|FAIL|N/A [details]

LAYER 2 RESULTS:
- Tests (frontend): PASS|FAIL|N/A [X passed, Y failed]
- Tests (backend): PASS|FAIL|N/A [X passed, Y failed]
- Tests (packages): PASS|FAIL|N/A [X passed, Y failed]
- TDD Coverage: PASS|WARN|BLOCK [list of findings]
- Cross-boundary: PASS|FAIL|N/A [details]

LAYER 3 RESULTS:
- Secrets: PASS|FAIL [details]
- Deprecated Patterns: PASS|FAIL|WARN [list of findings]
- File Sizes: PASS|WARN|FAIL [list of findings]

OVERALL: PASS|FAIL|WARN
BLOCKING ISSUES: [list or "none"]
WARNINGS: [list or "none"]
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
