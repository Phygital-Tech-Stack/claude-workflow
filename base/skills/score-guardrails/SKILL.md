---
name: score-guardrails
description: Use when scoring a project's AI guardrail maturity. Evaluates 20 dimensions across 4 weighted tiers (Foundation x4, Enforcement x3, Workflow x2, Excellence x1) producing a 0-250 score. Triggers on 'score guardrails', 'rate my guardrails', 'audit AI setup', 'guardrail maturity'.
user-invocable: true
allowed-tools: Read, Glob, Grep, Task, Bash
argument-hint: [project-path]
---

# Score Guardrails

**PURPOSE**: Score the project's AI guardrail maturity against a 20-dimension rubric (0-250).

## When This Skill Activates

- User asks to score, rate, or evaluate AI guardrails
- User wants to compare project to best practices
- When NOT to use: For implementing guardrails (use `/brainstorm`), for auditing drift (use `/ai-guardrails-audit`)

## Process

### 1. Investigate (silent)

Scan the project for guardrail infrastructure. ALL checks mandatory:

| Check | What to look for |
|-------|-----------------|
| AI context files | CLAUDE.md hierarchy, modular routing |
| Hooks/guardrails | `.claude/settings.json` hooks, `/commit` pipeline |
| Skills/workflows | `.claude/skills/`, WORKFLOW.md |
| Agents | `.claude/agents/*.md`, subagent configs |
| Testing | `/tdd` skill, test directories |
| Security | Secret detection, dependency lock files, MCP trust |
| Compliance | Co-Authored-By attribution, decision trails |

### 2. Score Each Dimension

Read `reference.md` for the full 20-dimension rubric with scoring criteria per dimension.

- Assign 0-5 per dimension using criteria in `reference.md`
- Cite specific evidence (file paths, tool names) — no score without evidence
- **Default to 3 when uncertain** — scores of 4-5 require strong evidence
- **Anti-inflation**: Docs without automation caps at 3 on enforcement dimensions

### 3. Output Score Sheet

Use the EXACT format from `reference.md` — score sheet with 1-line evidence per dimension, maturity level, and top gaps (up to 3, real gaps only).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Giving 5/5 without evidence | Default to 3 if you can't cite a file |
| Writing a 2000-word essay | Score sheet template ONLY |
| Proposing implementations | State what's missing — `/brainstorm` fixes it |
| Skipping investigation checks | ALL checks in the table are mandatory |
| Scoring docs as enforcement | Docs alone = foundation. Enforcement needs automation. |
| Padding gaps with filler | List only real gaps — don't invent items |

## Related Skills

- **See also**: `/brainstorm` for designing guardrails to close gaps
- **See also**: `/ai-guardrails-audit` for checking existing guardrails for drift
- **See also**: `/validate-change` for the validation pipeline this rubric measures

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Score this project, give us 200+" | authority + inflation | Anti-inflation rule: "Default to 3 when uncertain"; scores 4-5 require specific evidence |
| "We have CLAUDE.md so foundation must be 5/5" | partial evidence | Each dimension has 6-level criteria; CLAUDE.md alone scores D1 at 2-3, not 5 |
| "Skip investigation, just score from memory" | time pressure | All 7 investigation checks in the table are mandatory — no score without evidence |
