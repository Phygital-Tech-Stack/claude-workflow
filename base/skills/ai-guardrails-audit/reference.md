# AI Guardrails Audit - Deep Reference

## Diff-Based Scoping

Map changed file paths to the checks that need to run. In diff mode, only triggered checks execute.

```bash
# Get all changed files (staged + unstaged)
changed=$(git diff --name-only HEAD 2>/dev/null || git diff --name-only)
staged=$(git diff --name-only --cached)
all_changed=$(echo -e "$changed\n$staged" | sort -u | grep -v '^$')
```

### Path-to-Check Mapping

| Changed Path Pattern | Triggered Checks |
|---------------------|-----------------|
| `.claude/skills/*` | D1 |
| `.claude/agents/*` | D2 |
| `.claude/settings.json` | D3 |
| Package manager configs | D4 |
| Source directories | D5 |
| `.mcp.json` | D6 |
| `.claude/blueprints/*` | D7 |
| `CLAUDE.md` | D1, D2, D3, D4, D5, D6, D7 |
| `.claude/WORKFLOW.md` | D1, D2, D3 |

If no paths match any pattern, all deterministic checks are SKIP and only the agentic layer runs.

## D1: Skill Table Sync

### Source of Truth

```bash
# List all skill directories (each dir with SKILL.md = one skill)
ls -d .claude/skills/*/SKILL.md 2>/dev/null | sed 's|.claude/skills/||;s|/SKILL.md||'
```

### Check Location

- `CLAUDE.md` — "Available Skills" table
- `.claude/WORKFLOW.md` — "Core Skills" table

### Comparison

Compare skill directories against documented tables. Any skill NOT in both tables = WARN.

### --fix Pattern

Append missing skill row to CLAUDE.md Available Skills table.

## D2: Agent Table Sync

### Source of Truth

```bash
ls .claude/agents/*.md 2>/dev/null | sed 's|.claude/agents/||;s|\.md||'
```

### Comparison

Compare agent files against documented agent tables in CLAUDE.md and WORKFLOW.md.

## D3: Hook Coverage

### Source of Truth

```bash
.claude/hooks/pyrun -c "
import json
with open('.claude/settings.json') as f:
    data = json.load(f)
hooks = data.get('hooks', {})
total = 0
for event_type, hook_list in hooks.items():
    if isinstance(hook_list, list):
        total += len(hook_list)
print(f'Total hooks: {total}')
"
```

### Comparison

Use count ranges, not exact match. Settings.json has more granular hooks than WORKFLOW.md categories.

## D4: Tech Stack Sync

### Source of Truth

Extract dependencies from the project's package manager config file.

### Comparison

Flag NEW dependencies not mentioned in CLAUDE.md. Skip dev dependencies, internal packages, and build tooling.

## D5: Project Structure Sync

### Source of Truth

List source directories and compare against documented project structure in CLAUDE.md.

## D6: MCP Server Sync

### Source of Truth

```bash
.claude/hooks/pyrun -c "
import json
with open('.mcp.json') as f:
    data = json.load(f)
for name in data.get('mcpServers', {}):
    print(name)
" 2>/dev/null || echo "No .mcp.json found"
```

## D7: Blueprint File Sync

### Source of Truth

```bash
ls .claude/blueprints/*.md 2>/dev/null
```

Compare against documented blueprints in CLAUDE.md or WORKFLOW.md.

## Agentic Analysis

### Team Mode (3 Parallel Reviewers)

| Reviewer | Focus | Prompt |
|----------|-------|--------|
| **Toolchain** | Do tool versions, build configs, and CI match documentation? | Review toolchain alignment |
| **Conventions** | Do naming patterns and code style match documented conventions? | Review convention adherence |
| **Coherence** | Do CLAUDE.md, WORKFLOW.md, and skills tell a consistent story? | Review cross-document coherence |

### Dedup Logic

After all reviewers finish, deduplicate findings by file path. If multiple reviewers flag the same file, keep the most severe finding.

### Sequential Mode

Single subagent reviews all three dimensions. Slower but simpler. Use `--no-team` when parallelism isn't available.

## Verdict Templates

### PASS

```
## Guardrails Audit: PASS

All D-checks passed. Agentic reviewers found no drift.
Documentation is in sync with the codebase.
```

### WARN

```
## Guardrails Audit: WARN

| Check | Result | Detail |
|-------|--------|--------|
| D1-Skills | WARN | Missing: <skill-name> |
| D2-Agents | PASS | |
| ... | ... | |

### Recommendations
1. [Specific fix]
```

### STALE

```
## Guardrails Audit: STALE

Significant drift detected. N checks failed.

| Check | Result | Detail |
|-------|--------|--------|
...

### Priority Fixes
1. [Most impactful fix first]
```
