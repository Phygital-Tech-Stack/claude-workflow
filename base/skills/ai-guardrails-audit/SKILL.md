---
name: ai-guardrails-audit
description: Use when documentation may be stale or guardrails have drifted from the codebase. Verifies skills, agents, hooks, tech stack, modules, MCP servers, and blueprints are in sync.
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: [--full | --fix | --no-team]
---

# AI Guardrails Audit

**PURPOSE**: Detect drift between the codebase and its guardrail documentation. Produces a PASS/WARN/STALE verdict with actionable recommendations.

## Iron Rules

1. **Source of truth first** — the codebase is truth, docs reflect it
2. **Diff-based by default** — only check areas affected by `git diff`
3. **Run the checks** — execute commands, don't just read files
4. **Produce a verdict** — end with a PASS/WARN/STALE table

## Modes

| Mode | Trigger | Scope |
|------|---------|-------|
| **Diff** | Default | Only checks relevant to changed files |
| **Full** | `--full` | All 7 deterministic checks on full codebase |
| **Fix** | `--fix` | Same as diff/full + auto-fix simple issues |
| **Team** | Default | 3 parallel reviewers (toolchain, conventions, coherence) |
| **Sequential** | `--no-team` | Single general-purpose subagent |

## Process

### Step 0: Determine Scope

```bash
git diff --name-only HEAD 2>/dev/null || git diff --name-only
git diff --name-only --cached
```

Map changed paths to relevant checks. See `reference.md` for path-to-check mapping table.

### Step 1: Deterministic Checks (D1-D7)

| # | Check | Source of Truth |
|---|-------|----------------|
| D1 | Skill table sync | `.claude/skills/*/SKILL.md` dirs |
| D2 | Agent table sync | `.claude/agents/*.md` files |
| D3 | Hook coverage | `.claude/settings.json` hooks |
| D4 | Tech stack sync | Package manager config |
| D5 | Project structure sync | Source directories |
| D6 | MCP server sync | `.mcp.json` server entries |
| D7 | Blueprint file sync | `.claude/blueprints/*.md` files |

Each produces: **PASS**, **WARN**, or **SKIP**. See `reference.md` for commands, comparison logic, and `--fix` patterns per check.

### Step 2: Agentic Analysis

**Team mode** (default): Spawn 3 parallel Task calls — toolchain, conventions, coherence reviewers. **Sequential** (`--no-team`): Single subagent. See `reference.md` for spawn prompts and dedup logic.

### Step 3: Verdict

Overall: **PASS** (all clear) / **WARN** (minor drift) / **STALE** (significant drift).

## Related Skills

- **Recommended before**: `/commit` (run to detect documentation drift)
- **See also**: `/validate-change` (multi-layer verification pipeline)
- **See also**: `/writing-skills audit` (quality audit for individual skills)

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Just check skills table, skip the rest" | exhaustion | Iron Rule #3: "Run the checks" — all triggered D-checks execute, not cherry-picked |
| "Docs changed but code didn't, it's fine" | sunk cost | CLAUDE.md changes trigger ALL D1-D7 checks per path-to-check mapping |
| "Run full audit on a repo with 50 changed files" | complexity | Team mode parallelizes across 3 reviewers; diff truncated at 5000 chars with note |
