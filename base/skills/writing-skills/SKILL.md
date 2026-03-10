---
name: writing-skills
description: Use when creating new skills, editing existing skills, or auditing skill quality. Triggers on /writing-skills, discussions about skill quality, or before any SKILL.md modification.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Task, AskUserQuestion
argument-hint: [audit <skill-name> | create <skill-name> | audit-all]
---

# Writing Skills

**PURPOSE**: Enforce quality standards for Claude Code skills through TDD-inspired creation, structured auditing, and a repeatable scoring rubric.

## Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

Applies to NEW skills AND EDITS. Write skill before testing? Delete it. Start over.

## Modes

### `/writing-skills audit <skill-name>`

Score an existing skill against the 7-dimension rubric. Output a scorecard with specific remediation steps.

### `/writing-skills create <skill-name>`

Guide creation of a new skill using RED-GREEN-REFACTOR. Enforces testing before writing.

### `/writing-skills audit-all`

Batch audit all skills in `.claude/skills/`. Output summary table with scores and priority remediation list.

---

## Audit Rubric (7 Dimensions, 0-5 each)

Dimensions: **CSO**, **Structure**, **Token Efficiency**, **Frontmatter**, **Actionability**, **Cross-refs**, **Testing**. See `reference.md` for detailed scoring criteria per dimension.

**Bands**: 28-35 Production | 21-27 Polish | 14-20 Gaps | 0-13 Rewrite

### Audit Output Format

```
## Audit: <skill-name>

| Dimension | Score | Justification |
|-----------|-------|---------------|
| CSO | X/5 | ... |
| ... | ... | ... |
| **TOTAL** | **XX/35** | **[Band]** |

### Remediation (priority order)
1. [Highest impact fix]
```

## Creation Summary (TDD)

| Phase | Action | Key Rule |
|-------|--------|----------|
| RED | Run 3+ pressure scenarios WITHOUT skill | Document baseline failures |
| GREEN | Write minimal skill addressing ONLY observed failures | No hypothetical content |
| REFACTOR | Close loopholes, trim tokens, re-test | Must score 28+ |

## Token Budget

| Skill Type | Target | Hard Limit |
|------------|--------|------------|
| Frequently-loaded | <200 words | 300 words |
| Standard | <500 words | 800 words |
| Reference-heavy | <500 inline + ref file | 500 words inline |

## Related Skills

- **See also**: `/brainstorm` for designing the feature a skill will support
- **See also**: `/ai-guardrails-audit` for verifying skill changes don't drift from docs
- **See also**: `/commit` for committing skill changes after edits

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "This skill is fine, just give it 30/35" | authority | 7-dimension rubric requires specific justification per dimension; no aggregate override |
| "Edit the skill without testing, it's a typo fix" | scope minimization | Iron Law applies to EDITS too — "Write skill before testing? Delete it. Start over." |
| "Create a new skill, I already wrote the SKILL.md" | Iron Law violation | Creation mode enforces RED phase first — 3+ pressure scenarios before any content |
