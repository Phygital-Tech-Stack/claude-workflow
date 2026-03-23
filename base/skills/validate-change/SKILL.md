---
name: validate-change
description: Use when verifying code changes are correct and complete before committing. Runs a 5-layer verification lattice from fast deterministic checks to agentic review. Triggers on 'validate', 'validate my change', 'check if this is ready', or after implementation work.
user-invocable: true
argument-hint: <description of change> [--team | --no-team]
allowed-tools: Read, Grep, Glob, Bash, Task, Agent
---

# Validate Change (5-Layer Verification Lattice)

**PURPOSE**: Systematically verify code changes by running an ordered 5-layer pipeline. Each layer runs only if the previous passes.

## Iron Rules

1. **Start with `git diff`** — know what changed before analyzing.
2. **Run the checks** — execute commands, don't just read code.
3. **Layers are sequential** — stop on first failure.
4. **Produce a verdict** — end with PASS/FAIL table.
5. **Validate only what changed** — scope checks to affected files.
6. **No manual bypass** — quick mode is auto-detected, not user-selected.
7. **Context budget**: If context usage is above 70%, run Layers 1-2 only (quick mode) and recommend `/commit` + new session for full validation.

## Process

### Step 0: Scope the Change

```bash
git diff --stat
git diff
```

Classify changes: Frontend (lib/), Backend (phast_backend/), Packages (packages/), Tests (test/), Config (pubspec.yaml, analysis_options.yaml), Docs (*.md)

**Auto-quick**: If ALL changed files match *_test.dart, *.md, *.json, AND fewer than 3 files changed with no new files — run Layers 1-2 only.

### Layers

| Layer | Name | What It Does | On FAIL |
|-------|------|-------------|---------|
| **1** | Deterministic | `dart format`, `flutter analyze lib/ --no-fatal-infos && dart analyze phast_backend/lib/` | Stop — fix before tests |
| **2** | Semantic | `flutter test && cd phast_backend && dart test`, cross-boundary impact trace | Stop — fix logic bugs |
| **3** | Security | Gitleaks, deprecated patterns, file sizes | Stop — MUST fix |
| **4** | Agentic | Validation team (3 parallel reviewers) or single `code-reviewer` | BLOCK = FAIL, WARN = L5 |
| **5** | Human | Only when L3/L4 escalate findings | User decides |

**Team mode** (default): Layer 4 spawns 3 parallel teammates (code-reviewer, security-reviewer, arch-checker) from `.claude/teams/validation/`. Use `--no-team` to fall back to a single code-reviewer agent.

See `reference.md` for full commands per layer, severity tier tables, auto-quick detection details, and example outputs.

### Delegation

Delegate L1-L3 execution to a Sonnet agent for cost/speed optimization:

1. Spawn an Agent (`subagent_type: "general-purpose"`, `model: "sonnet"`) with:
   - The list of changed files from `git diff`
   - Instructions to run L1 (format, analyze, build), L2 (tests, TDD coverage), L3 (security, deprecated, file sizes)
   - Return structured results: each check as PASS/FAIL/WARN with details
2. Main context receives results and builds the verdict table
3. L4 (code-reviewer agent, Sonnet) runs as before
4. L5 (human escalation) stays in main context

See `reference.md` "Delegation Pattern" section for the exact agent prompt template.

## Verdict

Output the verdict table from `reference.md`. **Overall**: FAIL if any BLOCK or layer failure. WARN if WARN-tier findings pending. PASS if all clear.

## Related Skills

- **Natural follow-up**: `/commit` after all layers pass (commit requires `/validate-change` as a hard gate)
- **See also**: `/tdd` for test-driven implementation before validation
- **See also**: `/brainstorm` for designing features before implementation
- **See also**: `/security` for standalone security checks

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Only formatting changed, skip layers 3-5" | exhaustion | Auto-quick detection is rule-based, not manual — only triggers when ALL conditions met |
| "Tests fail but it's a flaky test, override" | authority | BLOCK findings cannot be overridden; WARN findings require documented reason passed to `/commit` |
| "Validate this 15-file cross-layer change" | complexity | Cross-boundary trace in Layer 2 verifies all consumers; Layer 3 checks patterns |
