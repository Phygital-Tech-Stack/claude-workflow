# Writing Skills - Deep Reference

## Audit Rubric — Scoring Criteria

| # | Dimension | 5 (Excellent) | 3 (Adequate) | 0 (Missing) |
|---|-----------|---------------|--------------|-------------|
| 1 | **CSO** | "Use when..." + symptoms, NO workflow summary | Has description but summarizes | Missing or generic |
| 2 | **Structure** | Overview, when-to-use, core pattern, quick ref | Some sections, inconsistent | Wall of text |
| 3 | **Token Efficiency** | <500 words, heavy ref in separate files | <800 words, some bloat | >1000 words |
| 4 | **Frontmatter** | name + description + allowed-tools, all correct | Has most fields | Missing |
| 5 | **Actionability** | Concrete steps, real commands, actual file paths | Mix of concrete and vague | Abstract only |
| 6 | **Cross-refs** | Explicit "REQUIRED: /skill" or "See: /skill" | Mentions informally | Isolated |
| 7 | **Testing** | Baseline tested, pressure scenarios documented | Informally tested | Never tested |

## TDD Skill Creation Guide

### RED Phase: Document Baseline Failures

Before writing ANY skill content:

1. **Identify 3+ pressure scenarios** that expose gaps without the skill
2. **Run each scenario** against Claude Code (or simulate)
3. **Document failures**: What went wrong? What was skipped? What was inconsistent?

Example pressure scenarios:
- Time pressure: "Just do it quickly"
- Authority override: "Skip that step, I know what I'm doing"
- Scope creep: "While you're at it, also do X"
- Exhaustion: "That's good enough, don't check everything"
- Sunk cost: "We already wrote the code, just commit it"

### GREEN Phase: Write Minimal Skill

Address ONLY the failures observed in RED phase:

1. Write SKILL.md with frontmatter
2. Include only steps that prevent observed failures
3. Add pressure-tested table documenting defenses
4. If content exceeds 500 words, extract to reference.md

**Key rule**: No hypothetical content. Every line must trace to an observed failure.

### REFACTOR Phase: Harden and Trim

1. Run pressure scenarios again WITH the skill
2. Close any remaining loopholes
3. Trim token count (target <500 words)
4. Add cross-references to related skills
5. Score against 7-dimension rubric — must achieve 28+/35

## Skill Template

```markdown
---
name: <kebab-case-name>
description: Use when <specific trigger conditions>. <What it does in one sentence>.
user-invocable: true
argument-hint: <expected arguments>
allowed-tools: <comma-separated tool list>
---

# /skill-name - Title

**PURPOSE**: <One sentence explaining the skill's goal>

## When This Skill Activates

<Specific trigger conditions — not a workflow summary>

## Process

### Step 1: <Action>

<Concrete steps with real commands>

### Step 2: <Action>

<More concrete steps>

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| ... | ... |

## Related Skills

- **REQUIRED**: `/other-skill` — <why required>
- **See also**: `/other-skill` — <when to use>

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| ... | ... | ... |
```

## CSO (Conditional Self-Organization) Guidelines

The `description` field in frontmatter is how Claude decides whether to load a skill. It must:

1. **Start with "Use when..."** — describes the trigger condition
2. **List symptoms** — observable conditions that indicate the skill is needed
3. **NOT summarize the workflow** — that goes in the body

### Good CSO Examples

```
description: Use when committing code changes after a work session. Supports session-scoped staging, lattice gate, code review, progress management, and conventional commits.
```

```
description: Use when verifying code changes are correct and complete before committing. Runs a 5-layer verification lattice.
```

### Bad CSO Examples

```
description: A skill for committing code.
```
(Too generic — when does it trigger?)

```
description: This skill runs git status, stages files, generates a conventional commit message, runs code review...
```
(Summarizes workflow instead of describing trigger)

## Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| Wall of text | Claude burns tokens reading, user can't scan | Split: <500 words SKILL.md + reference.md |
| Hypothetical content | Defends against problems that don't exist | RED phase first — only address observed failures |
| Missing frontmatter | Claude can't auto-trigger the skill | Add name, description, allowed-tools |
| Generic description | Claude triggers on wrong scenarios | "Use when..." with specific conditions |
| No pressure testing | Skill crumbles under real-world pressure | Document 3+ scenarios in pressure-tested table |
| Isolated skill | No cross-references; user doesn't know related skills | Add REQUIRED and See also sections |
| Stale commands | Commands reference files/tools that changed | Audit regularly with `/ai-guardrails-audit` |

## Red Flags During Audit

- Skill loads but user always has to correct its behavior → CSO mismatch
- Skill is >1000 words with no reference.md → needs splitting
- Skill references specific file paths that don't exist → stale
- Skill has no pressure-tested table → untested
- Skill description doesn't start with "Use when" → bad CSO
