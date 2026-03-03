# Claude Code Workflow

**Version:** {{VERSION}} | **Stacks:** {{STACKS}}

## The Problem

Without a defined workflow, the AI skips steps: implements without design, commits without validation, edits critical files without understanding impact. This leads to untested code, broken conventions, security gaps, and lost context across sessions.

## Workflow Overview

```
Feature Development
  /brainstorm ──▶ Plan Mode ──▶ /tdd ──▶ Implement ──▶ /validate-change ──▶ /commit

Bug Fix
  Investigate root cause ──▶ /tdd (failing test) ──▶ Fix ──▶ /validate-change ──▶ /commit

Quick Change (config, docs, minor fix)
  Edit ──▶ /validate-change --quick ──▶ /commit
```

## Components

### Auto-Triggered Guards (PreToolUse)

| Guard | Severity | Action |
|-------|----------|--------|
| **Env/secrets guard** | Advisory | Warns on credentials/config files |
| **Critical file guard** | Advisory | Warns on schema/migrations/infrastructure files |
| **Quick-fix blocker** | **Blocker** | Blocks hack/workaround/temp-fix comments |
| **Prompt injection detector** | Advisory | Warns on injection patterns (OWASP ASI01) |

### PostToolUse Hooks

| Hook | Action |
|------|--------|
| **Test reminder** | Reminds to run `/validate-change` after source file edits |
| **Session file tracker** | Tracks modified files to `.claude/session-files-{id}.txt` |

### Lifecycle Hooks

| Hook | Event Type | Purpose |
|------|------------|---------|
| **Session start** | SessionStart | Load progress context, inject git state, clean stale sessions |
| **Pre-compact** | PreCompact | Log compaction events for debugging |
| **Subagent context** | SubagentStart | Inject project rules and agent memory into specialist agents |
| **Task completed** | TaskCompleted | Count modified code files, remind to validate |
| **Failure handler** | PostToolUseFailure | Pattern-match errors, suggest recovery actions |
| **Teammate idle** | TeammateIdle | Check for active plans with remaining work |

### Core Skills

| Command | When to Use | Output |
|---------|-------------|--------|
| `/brainstorm <topic>` | New feature, architectural decision, significant refactor | Design doc in `docs/plans/1-draft/` |
| `/validate-change` | After implementing changes, before committing | 5-layer lattice verdict table |
| `/tdd <feature>` | When writing any code | Enforces RED-GREEN-REFACTOR cycle |
| `/commit` | After validation passes | Conventional commit with code review |
| `/ai-guardrails-audit` | Before doc updates, auto-invoked by /commit | Deterministic + agentic drift detection |
| `/security [scan\|deps\|owasp]` | Checking for vulnerabilities | Secret/dependency/auth audit |
| `/score-guardrails [path]` | Evaluating AI guardrail maturity | 20-dimension score sheet |
| `/writing-skills audit <name>` | Creating or editing a skill | Quality scorecard (28+/35 = production) |
| `/sync-workflow [--check\|--update]` | Sync workflow files from master | Drift report and auto-update |

### Specialized Agents

| Agent | Purpose |
|-------|---------|
| **code-reviewer** | Full-stack code review: auto-fix safe issues, report complex ones |

> Projects add domain-specific agents (security-reviewer, database-expert, etc.) in `.claude/agents/`.

## Session Continuity Lifecycle

```
Session Start                    Active Development                    Session End
     |                                  |                                  |
     v                                  v                                  v
[SessionStart hook]             [PostToolUse hooks]                  [/commit skill]
  - Read progress files          - Track files in session-files.txt   - Read session-files.txt
  - Extract "Next Session        - Auto-validate source files         - Stage tracked files
    Should" items                - Guard patterns & sizes             - Write progress file
  - Inject git branch +                                               - Clean session state
    last 3 commits
  - Clean stale session files
     |                                  |
     v                                  v
[SubagentStart hook]            [PreToolUse guards]
  - Inject project rules         - Guard secrets/env files
  - Load agent MEMORY.md         - Guard critical infra files
                                 - Block quick-fix markers
                                 - Detect prompt injection
```

### Session File Tracking

Every file written or edited is automatically recorded in `.claude/session-files-{session_id}.txt`. This enables:
- **Precise staging**: `/commit` stages only session-relevant files
- **Task metrics**: TaskCompleted hook counts modified code files
- **Audit trail**: Know exactly what changed in each session

Session files are auto-cleaned after 7 days by the SessionStart hook.

### Agent Memory

Persistent learning files live in `.claude/agent-memory/{agent}/MEMORY.md`. Agents receive their memory at spawn via the SubagentStart hook and should update it when discovering new patterns.

### Compaction Resilience

These artifacts persist outside the conversation context and survive compression:
- `.claude/progress/*.md` — session progress files
- `.claude/decisions.log` — architectural decision trail
- `.claude/agent-memory/*/MEMORY.md` — agent learning
- `.claude/session-files-*.txt` — current session file tracking
- `docs/plans/3-in-progress/*-progress.md` — active plan progress

## Detailed Workflows

### 1. New Feature (Full Workflow)

```
Step 1: /brainstorm <feature>
        ├── Claude reads codebase silently (Phase 1: Recon)
        ├── Asks questions one at a time (Phase 2: Understanding)
        ├── Presents 2+ approaches with trade-offs (Phase 3)
        ├── Walks through design in 200-300 word sections (Phase 4)
        ├── Saves design doc to docs/plans/1-draft/ (Phase 5)
        └── Offers: implement now (plan mode) or park for later (Phase 6)

Step 2: Plan Mode (EnterPlanMode)
        ├── Check progress file for prior session state
        ├── Explores codebase for implementation details
        ├── Plans file-level changes
        ├── Gets user approval before writing code
        └── TaskCreate for every step + write steps to progress file

Step 3: /tdd <feature> (TDD Cycle)
        ├── Write failing tests FIRST (RED)
        ├── Implement minimum code to pass (GREEN)
        ├── Refactor while tests stay green (REFACTOR)
        └── After each logical unit, run lint + tests immediately

Step 4: Implement
        ├── Write code following project patterns
        ├── HOOKS fire automatically (guards + reminders)
        ├── Create/update tests alongside code
        └── After each logical unit:
            ├── TaskUpdate (mark step completed)
            ├── Update progress file
            └── Run incremental validation

Step 5: /validate-change (5-Layer Lattice)
        ├── Layer 1 DETERMINISTIC: lint + typecheck
        ├── Layer 2 SEMANTIC: tests + cross-boundary impact
        ├── Layer 3 SECURITY: invoke /security scan
        ├── Layer 4 AGENTIC: invoke code-reviewer agent
        └── Layer 5 HUMAN: only if layers 3-4 escalate

Step 6: /commit
        ├── Identify session-relevant changes
        ├── Documentation staleness check
        ├── Lattice check (warn if /validate-change not run)
        ├── Code review via code-reviewer agent
        ├── Stage + conventional commit
        ├── Update progress file if active
        └── Verify with git log
```

### 2. Bug Fix (Root-Cause Required)

```
Step 1: Investigate
        ├── Reproduce (write a failing test)
        ├── Isolate (narrow to file:function)
        ├── Root cause (5 Whys)
        ├── Fix (via /tdd — failing test goes green)
        └── Verify (/validate-change + regression check)
Step 2: /commit
```

### 3. Skill Maintenance

```
Step 1: /writing-skills audit <skill-name>   → scorecard
Step 2: Fix issues identified in scorecard
Step 3: /writing-skills audit <skill-name>   → verify 28+/35
Step 4: /commit
```

## Agent Interaction Patterns

### Escalation Rules

When an agent encounters a concern outside its domain, it **flags but does not fix**. The orchestrator (Claude) decides whether to invoke the appropriate specialist agent.

### Inter-Agent Security (OWASP ASI07)

| ASI07 Risk | Mitigation |
|------------|------------|
| Privilege escalation via chain | Each agent has its own `allowed-tools` list; sub-agents do NOT inherit parent tools |
| Context poisoning between agents | SubagentStart hook injects fresh project rules; agents don't share mutable state |
| Unauthorized lateral movement | Agents communicate only through the orchestrator; no direct agent-to-agent messaging |
| Agent impersonation | Agent names validated at spawn time; only defined agents can be invoked |
| Excessive agency accumulation | Review agents are read-only — no Edit/Write/Bash tools |

## Development Principles

- **TDD**: Write failing test first, then implement. No code without a test.
- **YAGNI**: Don't build what isn't needed. Three similar lines > premature abstraction.
- **Root-cause debugging**: Fix the cause, not the symptom. No `// hack` or `// temp fix`.
- **Validate before commit**: Always run `/validate-change` before `/commit`.
- **Session continuity**: Update progress files so the next session knows where you left off.

## Quick Reference

| Scenario | Start With | Then |
|----------|-----------|------|
| "I have an idea for a feature" | `/brainstorm` | Plan mode → `/tdd` → implement → `/validate-change` → `/commit` |
| "Fix this bug" | Investigate root cause | `/tdd` → fix → `/validate-change` → `/commit` |
| "Check if my changes are safe" | `/validate-change` | `/commit` if all layers PASS |
| "Are my docs up to date?" | `/ai-guardrails-audit` | Fix drift → `/commit` |
| "Run a security check" | `/security scan` | Fix findings → `/validate-change` → `/commit` |
| "Commit my work" | `/commit` | — |
| "This skill isn't working well" | `/writing-skills audit` | Fix → re-audit → `/commit` |
| "How mature are my AI guardrails?" | `/score-guardrails` | Review gaps → `/brainstorm` to close them |
| "Sync workflow from master" | `/sync-workflow --check` | `/sync-workflow --update` if behind |

## Sync Management

This workflow is managed by the [claude-workflow](https://github.com/Phygital-Tech-Stack/claude-workflow) master repository.

- **Lock file**: `.claude/workflow.lock` — tracks managed files and their checksums
- **Overrides**: `.claude/workflow.overrides.yaml` — project-specific configuration
- **Drift check**: Run `/sync-workflow --check` to detect drift from master
- **Update**: Run `/sync-workflow --update` to pull updates from master

Files listed in `workflow.overrides.yaml` → `exclude` are project-owned and never overwritten by sync.

## Reference

- **Agent definitions**: `.claude/agents/*.md`
- **Agent memory**: `.claude/agent-memory/*/MEMORY.md`
- **Skill definitions**: `.claude/skills/*/SKILL.md`
- **Hook scripts**: `.claude/hooks/*.sh`, `.claude/hooks/*.py`
- **Settings**: `.claude/settings.json`
- **Session file tracking**: `.claude/session-files-*.txt`
- **Decision log**: `.claude/decisions.log`
- **Compaction log**: `.claude/compaction.log`
- **Session progress**: `.claude/progress/`
- **Active plans**: `docs/plans/3-in-progress/*-progress.md`
- **Blueprints**: `.claude/blueprints/`
