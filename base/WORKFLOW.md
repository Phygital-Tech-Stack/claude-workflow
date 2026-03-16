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

### Agents

| Agent | Purpose | Model | Read-only? |
|-------|---------|-------|------------|
| **code-reviewer** | Full-stack code review: auto-fix safe issues, report complex ones | opus | No |
| **planner** | Break complex features into parallelizable tasks | opus | Yes |
| **backend-handler** | Implement backend API modules | sonnet | No |
| **frontend-handler** | Implement frontend components and screens | sonnet | No |
| **test-writer** | Write comprehensive tests for implemented features | sonnet | No |
| **security-reviewer** | Security-focused review, OWASP compliance | opus | Yes |
| **db-expert** | Database schema review and migration guidance | sonnet | Yes |

### Agent Orchestration

For complex features, the orchestrator (Claude) coordinates specialist agents:

```
Orchestrator (Claude)
  ├── Phase 1: planner → implementation plan with task graph
  ├── Phase 2 (parallel):
  │     ├── backend-handler → implements API layer
  │     ├── frontend-handler → implements UI components
  │     └── test-writer → writes tests
  ├── Phase 3 (parallel):
  │     ├── security-reviewer → security audit
  │     └── code-reviewer → convention audit
  └── Phase 4: Orchestrator merges findings → /commit
```

**When to use parallel vs sequential:**

| Criteria | Use Parallel | Use Sequential |
|----------|-------------|----------------|
| Tasks share no files | Yes | — |
| Task B reads Task A's output | — | Yes |
| Agents are read-only | Yes | — |
| Tight coupling between components | — | Yes |
| Large feature (>5 files) | Yes | — |

### How to Invoke Parallel Agents

**Worked example: "Adding a user profile endpoint"**

```
Step 1: Invoke planner agent
        Task(planner, "Plan user profile endpoint: GET/PUT /users/:id/profile")
        → Returns task graph with disjoint file sets per agent

Step 2: Spawn parallel handlers (no shared files)
        Task(backend-handler, "Implement profile model + handler per plan step backend.*")
        Task(frontend-handler, "Implement ProfileScreen + useProfile hook per plan step frontend.*")
        Task(test-writer, "Write unit + integration tests per plan step tests.*")
        ← All three run concurrently — they touch separate file trees

Step 3: Spawn parallel reviewers (read-only, safe to parallelize)
        Task(security-reviewer, "Audit profile endpoint for auth, data exposure, OWASP top 10")
        Task(code-reviewer, "Review profile implementation against coding conventions")
        ← Both are read-only — no conflict risk

Step 4: Orchestrator merges findings
        ├── Apply auto-fixes from code-reviewer
        ├── Address security-reviewer findings
        ├── Run /validate-change
        └── /commit
```

> **Key rule**: Only spawn agents in parallel when they touch **disjoint file sets**. If two agents might edit the same file, run them sequentially.

### Troubleshooting Parallel Agents

| Problem | Symptom | Resolution |
|---------|---------|------------|
| **Conflicting file edits** | Two agents edit the same file; second write overwrites the first | Run conflicting agents sequentially, or split the file into separate modules before parallelizing |
| **Agent timeout/failure** | An agent fails or stalls; other agents completed successfully | Re-invoke only the failed agent with the same prompt. Do not re-run successful agents. Check agent memory for known error patterns |
| **Context budget exceeded** | Parallel agents multiply context cost (N agents × prompt size); orchestrator hits limits | Reduce parallelism — run 2 agents at a time instead of 5. Use `/compact` between phases. Keep agent prompts focused (reference plan steps, not full plan) |

> Projects can exclude unused agents via `workflow.overrides.yaml` → `exclude`.

### Model Routing

Agents use either **opus** (judgment-heavy) or **sonnet** (execution-heavy) based on their role:

| Role Type | Model | Agents | Rationale |
|-----------|-------|--------|-----------|
| **Planning & review** | opus | planner, code-reviewer, security-reviewer | Requires nuanced judgment, architectural reasoning, risk assessment |
| **Implementation** | sonnet | backend-handler, frontend-handler, test-writer, db-expert | Execution against clear specs; speed and cost efficiency matter |

**Cost**: Opus is ~5x the cost of Sonnet. Default to Sonnet unless the task requires judgment that Sonnet consistently gets wrong.

**Override per-project**: Set `model_overrides` in `workflow.overrides.yaml`:

```yaml
model_overrides:
  code-reviewer: sonnet    # downgrade for cost-sensitive projects
  test-writer: opus        # upgrade for complex test scenarios
```

**Fallback**: If the primary model is unavailable, agents fall back to the next available model in the same tier. No cross-tier fallback by default — a review agent should not silently downgrade to Sonnet.

<!-- PROJECT: Add project-specific agents here. -->

### Core Skills

| Command | When to Use | Output |
|---------|-------------|--------|
| `/brainstorm <topic>` | New feature, architectural decision, significant refactor | Design doc in `docs/plans/1-draft/` |
| `/validate-change` | After implementing changes, before committing | 5-layer lattice verdict table |
| `/tdd <feature>` | Full TDD ceremony (test-first is automatic by default) | Enforces RED-GREEN-REFACTOR cycle |
| `/commit` | After validation passes | Conventional commit with code review |
| `/ai-guardrails-audit` | Before doc updates, auto-invoked by /commit | Deterministic + agentic drift detection |
| `/security [scan\|deps\|owasp]` | Checking for vulnerabilities | Secret/dependency/auth audit |
| `/score-guardrails [path]` | Evaluating AI guardrail maturity | 20-dimension score sheet |
| `/writing-skills audit <name>` | Creating or editing a skill | Quality scorecard (28+/35 = production) |
| `/sync-workflow [--check\|--update]` | Sync workflow files from master | Drift report and auto-update |

<!-- PROJECT: Add project-specific skills here. Example:
| `/deploy` | Production deployment | Build, package, deploy with health checks |
| `/pull-logs` | Collect production logs | Organized log files for debugging |
-->

### Auto-Triggered Guards (PreToolUse)

| Guard | Type | Severity | Action |
|-------|------|----------|--------|
| **Env/secrets guard** | command | Advisory | Warns on credentials/config files |
| **Critical file guard** | prompt | Advisory | LLM judges if file is critical infrastructure |
| **Quick-fix guard** | command | Steering | Warns on hack/workaround/temp-fix comments |
| **Prompt injection detector** | command | Advisory | Warns on injection patterns (OWASP ASI01) |
| **Scope estimator** | prompt | Advisory | LLM warns on high blast radius changes (>5 files) |
| **MCP security scan** | command | **Blocker**/Advisory | Blocks if `mcp-scan` missing; warns on CVE findings |

**Hook types**: `command` — deterministic shell/Python checks. `prompt` — LLM judgment without file access. `agent` — LLM with codebase read access (opt-in via stack overlays, heavy).

> The `critical-file-agent` guard (type: agent) is available in `base/guards/` but not enabled by default due to performance cost. Stacks can opt in via their `settings.overlay.json`.

### PostToolUse Hooks

| Hook | Severity | Action |
|------|----------|--------|
| **Test reminder** | Advisory | Reminds to run `/validate-change` after source file edits |
| **Session file tracker** | Silent | Tracks modified files to `.claude/session-files-{id}.txt` |

<!-- PROJECT: Add stack-specific PostToolUse hooks here. Example (flutter-dart):
| `dart_format.py` | Auto-fix | Auto-format Dart files |
| `dart_analyze.py` | Advisory | Auto-analyze Dart files after edits |
| `check_file_size.py` | **Blocker**/Advisory | Block screens >1000 lines, warn >600 |
-->

### Lifecycle Hooks

| Hook | Event Type | Purpose |
|------|------------|---------|
| **Session start** | SessionStart | Load progress context, inject git state, clean stale sessions |
| **MCP security scan** | SessionStart | Scan `.mcp.json` for known CVEs via `mcp-scan` |
| **Prompt submit** | UserPromptSubmit | Inject git branch/commit, active progress, warn on dangerous patterns |
| **Pre-compact** | PreCompact | Log compaction events for debugging |
| **Subagent context** | SubagentStart | Inject project rules and agent memory into specialist agents |
| **Subagent stop** | SubagentStop | Warn if subagent output is empty or contains failure indicators |
| **Task completed** | TaskCompleted | Count modified code files, remind to validate |
| **Failure handler** | PostToolUseFailure | Pattern-match errors, suggest recovery actions |
| **Teammate idle** | TeammateIdle | Check for active plans with remaining work |
| **Session end** | SessionEnd | Warn on unvalidated/uncommitted code, log session metrics |

### Steering Philosophy

Guards default to **steer, don't block** — warn the agent and let downstream validation catch unresolved issues.

| Behavior | Output | Exit | When to use |
|----------|--------|------|-------------|
| **Steer** | `systemMessage` | 0 | Default for all guards |
| **Block** | `decision: block` | 2 | Hard structural limits (file size), expensive-to-reverse changes |

**Severity labels:**

| Label | Meaning |
|-------|---------|
| `[STEER]` | Guidance — proceed with care |
| `[GUARD]` | Infrastructure alert |
| `[SECURITY]` | Security advisory |
| `[BOUNDARY]` | Architecture violation |
| `[ROOT-CAUSE] BLOCKED` | Hard stop (reserved for blockers) |

### Blueprints

Deep-reference documents in `.claude/blueprints/` used by skills as authoritative sources:

| Blueprint | Purpose | Used By |
|-----------|---------|---------|
| `coding-conventions.md` | Naming, file limits, banned patterns, extraction rules | `/validate-change`, `/commit`, `code-reviewer` agent |
| `testing-patterns.md` | Test organization, mock patterns, per-layer testing | `/tdd`, `code-reviewer` agent |
| `api-contracts.md` | Handler patterns, response shapes, endpoint mapping | `/validate-handler` (if present) |

<!-- PROJECT: Add project-specific blueprints here. -->

### Teams

Curated prompt bundles for coordinated parallel agent orchestration. Teams complement the official (experimental) Claude Code Agent Teams runtime — we provide project-level prompt templates and roster configs.

| Team | Scope | Members | Used By |
|------|-------|---------|---------|
| **validation** | Base (all projects) | code-reviewer, security-reviewer, arch-checker | `/validate-change --team` |
| **generation** | Stack-specific | Varies by stack (e.g., schema-builder, backend-builder, api-builder, test-writer) | `/generate-module --team` (planned) |

**Structure**: Each team lives in `.claude/teams/<name>/` with:
- `team.yaml` — thin manifest (name, description, member list)
- `README.md` — usage documentation and orchestration patterns
- `prompts/<member>.md` — self-contained prompt for each teammate

**Relationship to agents**: Teams reference standalone agents by name (from `.claude/agents/`). Teams can also define team-only specialists via `prompts/<name>.md` that don't exist as standalone agents.

**Sync**: Base teams come from `base/teams/`. Stack-specific teams come from `stacks/{stack}/teams/`. Stack teams overlay base teams (stack wins on conflict).

## Session Continuity Lifecycle

```
Session Start                    Active Development                    Session End
     |                                  |                                  |
     v                                  v                                  v
[SessionStart hook]             [PostToolUse hooks]                  [SessionEnd hook]
  - Read progress files          - Track files in session-files.txt   - Check for unvalidated code
  - Extract "Next Session        - Auto-validate source files         - Warn on uncommitted changes
    Should" items                - Guard patterns & sizes             - Log session metrics
  - Inject git branch +                                                    |
    last 3 commits                                                         v
  - Clean stale session files                                        [/commit skill]
  - MCP security scan
     |                                  |                              - Read session-files.txt
     v                                  v                              - Stage tracked files
[UserPromptSubmit hook]         [PreToolUse guards]                    - Write progress file
  - Inject git branch/commit     - Guard secrets/env files             - Clean session state
  - Flag active progress         - Guard critical infra (prompt)
  - Warn on dangerous patterns   - Steer on quick-fix markers
     |                           - Detect prompt injection
     v                           - Estimate change scope (prompt)
[SubagentStart hook]
  - Inject project rules
  - Load agent MEMORY.md
```

### Session File Tracking

Every file written or edited is automatically recorded in `.claude/session-files-{session_id}.txt`. This enables:
- **Precise staging**: `/commit` stages only session-relevant files
- **Task metrics**: TaskCompleted hook counts modified code files
- **Audit trail**: Know exactly what changed in each session

Session files are auto-cleaned after 7 days by the SessionStart hook.

### Agent Memory

Persistent learning files live in `.claude/agent-memory/{agent}/MEMORY.md`. Agents receive their memory at spawn via the SubagentStart hook and should update it when discovering new patterns.

### Auto-Memory vs Agent-Memory

Claude Code maintains auto-memory (in `~/.claude/projects/` per project) that captures build commands, debugging insights, and codebase patterns automatically. This is separate from the workflow's managed agent-memory.

| Memory Type | Source | Reviewed? | Best For |
|-------------|--------|-----------|----------|
| **Agent MEMORY.md** | Claude (curated) | Human-reviewable | Persistent agent-specific learnings |
| **Auto-memory** | Claude (automatic) | Not reviewed | Build commands, debug insights, patterns |
| **Progress files** | Claude (structured) | Human-reviewable | Session handoff, next steps |

**Policy**: Auto-memory supplements but does not replace agent-memory. If auto-memory contradicts agent-memory, agent-memory wins (it's curated). Do not manually edit auto-memory files — they are Claude Code-managed. Do manually curate `.claude/agent-memory/*/MEMORY.md`.

### Compaction Resilience

These artifacts persist outside the conversation context and survive compression:
- `.claude/progress/*.md` — session progress files
- `.claude/decisions.log` — architectural decision trail
- `.claude/agent-memory/*/MEMORY.md` — agent learning
- `.claude/session-files-*.txt` — current session file tracking
- `docs/plans/3-in-progress/*-progress.md` — active plan progress

## Context Window Management

Context fills fast, and performance degrades as it fills. The `context-check.sh` hook monitors usage automatically.

### Compact Trigger Thresholds

| Context Usage | Action |
|--------------|--------|
| **>60%** | Consider `/compact` before starting a new feature |
| **>80%** | `/compact` before running `/validate-change` (results degrade otherwise) |
| **>90%** | **Mandatory** `/compact` — do not commit from this state |

### Session Scope

One session = one logical unit of work. For large features:
1. Break into steps via plan mode
2. Complete one step per session
3. `/commit` progress, write progress file with "Next Session Should" items
4. Start a fresh session for the next step

### Pre-Compact Checklist

Before compacting (or when context is high):
1. Update progress file with current state
2. `/commit` if there are working changes
3. Log key decisions to `.claude/decisions.log`

### Compaction Report

Run `python3 tools/compaction_report.py` to review compaction history from `.claude/compaction.log`. The report shows total compactions, average context % at compaction time, and the most recent event. Use `--format json` for machine-readable output.

### Token-Heavy Operations

- `/brainstorm` — spawns multi-phase analysis. If context >60%, consider parking the design doc and continuing in a new session.
- `/validate-change` Layer 4 (agentic) — spawns sub-agent. If context >70%, use `--quick` mode (Layers 1-2 only).

## Detailed Workflows

### 1. New Feature (Full Workflow)

```
Step 1: /brainstorm <feature>
        ├── Claude reads codebase silently (Phase 1: Recon)
        ├── Asks questions one at a time (Phase 2: Understanding)
        ├── Presents 2+ approaches with trade-offs (Phase 3)
        ├── Walks through design in 200-300 word sections (Phase 4)
        ├── Saves design doc to docs/plans/1-draft/ (Phase 5)
        └── Phase 6 Handoff:
            ├── Path A: Implement now → move to 3-in-progress/ → Plan Mode
            └── Path B: Park for later → move to 2-approved/

Step 2: Plan Mode (EnterPlanMode)
        ├── If resuming from 2-approved/, move to 3-in-progress/ first
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
        ├── Move completed plans: 3-in-progress/ → 4-done/
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

- **TDD**: Write failing test first, then implement. Test-first is the default; use `/tdd` for the full ceremony.
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
| "Clean up after implementation" | `/simplify` | Review changed code for reuse, quality, efficiency → auto-fix |
| "Bulk changes across files" | `/batch <instruction>` | Applies instruction to multiple files in one pass |
| "Continuous background checks" | `/loop 20m /validate-change` | Runs command on interval — stop with `/loop stop` |
| "Sync workflow from master" | `/sync-workflow --check` | `/sync-workflow --update` if behind |
| "Large feature, multiple agents" | `Task(planner, ...)` | Parallel handlers → reviewers → `/validate-change` → `/commit` |

## Sync Management

This workflow is managed by the [claude-workflow](https://github.com/Phygital-Tech-Stack/claude-workflow) master repository.

- **Lock file**: `.claude/workflow.lock` — tracks managed files and their checksums
- **Overrides**: `.claude/workflow.overrides.yaml` — project-specific configuration
- **Drift check**: Run `/sync-workflow --check` to detect drift from master
- **Update**: Run `/sync-workflow --update` to pull updates from master

Files listed in `workflow.overrides.yaml` → `exclude` are project-owned and never overwritten by sync.

## Tool Integrations

### MCP Servers (`.mcp.json`)

MCP templates are per-stack in `stacks/{stack}/.mcp.json.template`. `init.sh` merges templates from all selected stacks and resolves tokens from environment variables.

| Server | Stacks | Domain | Access |
|--------|--------|--------|--------|
| **pharos** | typescript-nestjs, python-fastapi | SYSPRO, Tempo MRP, PhX — live schema, KPI dashboards | Read/Write |
| **context7** | all | Up-to-date documentation lookup for NestJS, FastAPI, Flutter, .NET | Read-only |
| **chrome-devtools** | flutter-dart | Screenshot capture, visual regression, DOM inspection | Read-only |
| **github** | typescript-nestjs | PR context, issue details during code review | Read-only |

**Setup**: Set `PHAROS_TOKEN` and `GITHUB_TOKEN` environment variables before running `init.sh`. The generated `.mcp.json` is gitignored (contains tokens).

> **Security**: `mcp-security-scan.sh` runs at session start via `mcp-scan`. Requires `mcp-scan` (`pip install mcp-scan`). Findings are advisory — review before using MCP tools.

### CLI Tools (via Bash allowlist)

| Tool | Domain | Used By | Permission |
|------|--------|---------|------------|
| `git` | Version control | All hooks, `/commit` | Auto-allowed |
| Stack formatter | Code formatting | PostToolUse hooks | Auto-allowed |
| Stack analyzer | Static analysis | PostToolUse hooks, `/validate-change` | Auto-allowed |
| Stack test runner | Testing | `/tdd`, `/validate-change` | Auto-allowed |

### Visual Verification (flutter-dart)

For UI work in Flutter, use the DevTools MCP server (auto-configured in flutter-dart stack) for screenshot-based verification:

```
Edit widget → Hot reload → Screenshot → Compare to baseline → Iterate
```

Baseline screenshots live in `docs/screenshots/`, named after the screen/component. `/validate-change` Layer 2 includes a visual check step for flutter-dart stacks.

**Tools**: The `chrome-devtools` MCP server is included in the flutter-dart `.mcp.json.template`. Use `tools/screenshot_diff.sh <baseline> <current>` to compare screenshots via ImageMagick (exit 0 = match, exit 1 = diff).

<!-- PROJECT: Add project-specific CLI tools here. -->

> Projects should document their full tool inventory here for audit and onboarding purposes.

## CI/CD Integration

Claude Code can review PRs automatically via GitHub Actions or GitLab CI.

### Setup

1. Run `init.sh --ci` to install the CI template for your platform
2. Add `ANTHROPIC_API_KEY` to your repository secrets
3. Set `ci_enabled: true` in projects.json for tracking

### Available Templates

| Template | Platform | Trigger |
|----------|----------|---------|
| `claude-pr-review.yml` | GitHub Actions | PR opened/updated, `@claude` comment |
| `claude-mr-review.yml` | GitLab CI | MR pipeline |

### What CI Review Does

1. Reads project blueprints (coding-conventions.md, testing-patterns.md)
2. Reviews changed files against conventions
3. Checks for missing tests, security concerns
4. Posts review comments with BLOCK/WARN/INFO severity

> **Note**: CI review complements local `/validate-change` — it catches issues from PRs opened outside the workflow.

## Scheduled Automation

Claude Code's `/loop` command runs any prompt or slash command on a recurring interval — enabling continuous background validation without manual invocation.

### Usage

```
/loop [interval] <command>    Start a recurring loop (default: 10m)
/loop stop                    Stop the active loop
```

### Patterns

| Pattern | Interval | Purpose |
|---------|----------|---------|
| `/loop 20m /validate-change` | 20 min | Continuous validation during implementation |
| `/loop 30m /security scan` | 30 min | Periodic security checks during long sessions |
| `/loop 15m /sync-workflow --check` | 15 min | Drift monitoring against master workflow |

### When to Use

- **Long implementation sessions** — catch regressions early without interrupting flow
- **Security-sensitive work** — continuous scanning for leaked secrets or dependency issues
- **Multi-session features** — monitor drift between your branch and master workflow

### When NOT to Use

- **Short tasks** — manual invocation is faster and cheaper
- **High context usage (>70%)** — each loop iteration consumes tokens; prefer manual checks
- **Token-constrained environments** — loops accumulate cost over time

### Context Budget Warning

Each loop iteration runs within the current conversation context. At 20-minute intervals over a 2-hour session, that's 6 invocations — plan your context budget accordingly. Use `/compact` between heavy loop iterations if context exceeds 60%.

## Reference

- **Agent definitions**: `.claude/agents/*.md`
- **Agent memory**: `.claude/agent-memory/*/MEMORY.md` (persistent learning per agent)
- **Skill definitions**: `.claude/skills/*/SKILL.md`
- **Hook scripts (Python)**: `.claude/hooks/*.py` (PostToolUse validators)
- **Hook scripts (Shell)**: `.claude/hooks/*.sh` (lifecycle hooks)
- **Settings**: `.claude/settings.json` (hook registrations, permissions)
- **Session file tracking**: `.claude/session-files-*.txt` (auto-cleaned after 7 days)
- **Decision log**: `.claude/decisions.log`
- **Compaction log**: `.claude/compaction.log`
- **Session progress**: `.claude/progress/`
- **Plan lifecycle**: `docs/plans/LIFECYCLE.md`
- **Draft plans**: `docs/plans/1-draft/`
- **Approved plans**: `docs/plans/2-approved/`
- **Active plans**: `docs/plans/3-in-progress/*-progress.md`
- **Completed plans**: `docs/plans/4-done/`
- **Abandoned plans**: `docs/plans/5-archive/`
- **Blueprints**: `.claude/blueprints/`
