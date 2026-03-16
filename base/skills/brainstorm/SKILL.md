---
name: brainstorm
description: Use when unsure how to approach a feature, or when you want to evaluate trade-offs before coding. Explores intent, constraints, and alternatives before implementation.
user-invocable: true
argument-hint: <idea or feature description>
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion, EnterPlanMode
model: opus
---

# Brainstorm Skill

**PURPOSE**: Turn rough ideas into validated, implementation-ready designs through structured collaborative dialogue. Prevents wasted effort by exploring intent, constraints, and alternatives before writing code.

## When This Skill Activates

1. User invokes `/brainstorm` or `/brainstorm <topic>`
2. User describes a new feature or capability they want to build
3. User says "I have an idea" or "what if we..." or "I'm thinking about..."
4. User wants to explore architectural options before committing
5. User is planning a significant refactor or redesign

## Core Principles

1. **One question at a time** — Never overwhelm with multiple questions
2. **Prefer multiple-choice** — Offer 2-3 options with trade-offs
3. **YAGNI ruthlessly** — Challenge features that aren't immediately needed
4. **Explore before settling** — Present at least 2 approaches with trade-offs
5. **Validate incrementally** — Present design in digestible sections, confirm each
6. **Code reads before opinions** — Examine actual codebase before assuming
7. **Use AskUserQuestion for every question** — Never print a question as text. Always use AskUserQuestion with 2-4 options.

## The Process (6 Phases)

### Phase 1: Autonomous Recon (silent)

Before asking questions: read relevant CLAUDE.md files, search codebase for related code, check `docs/plans/` for previous designs, check git log. Output a brief summary, then your first question.

### Phases 2-6 (see `reference.md` for full detail)

| Phase | Goal | Output |
|-------|------|--------|
| 2. Understanding | _Why_ before _what_ — purpose, scope, constraints, success criteria | Clear problem statement |
| 3. Approaches | At least 2 options with trade-offs, effort, files touched | Chosen approach |
| 4. Design | 200-300 word sections, validated incrementally | Approved design |
| 5. Documentation | Save to `docs/plans/1-draft/YYYY-MM-DD-HHmm-<topic>-design.md` | Design doc committed |
| 6. Handoff | Implement now (EnterPlanMode) or park for later | Next step decided |

## Key Rules

- **Never write implementation code** — design doc only. Use plan mode for implementation.
- **Small idea?** Skip brainstorming — just use plan mode or implement directly.
- **Context budget**: If context usage is above 60%, recommend parking the design doc and continuing in a new session rather than spawning the full 6-phase process.

## Related Skills

- **See also**: `/tdd` for test-first implementation after plan approval
- **See also**: `/validate-change` for validation after implementation
- **See also**: `/ai-guardrails-audit` for verifying design docs don't drift from guardrails
- **See also**: `/commit` for committing changes

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Just build it, no need to brainstorm a simple button" | YAGNI test | Key Rules: "Small idea? Skip brainstorming" — skill self-selects out for trivial work |
| "I've already decided the approach, just document it" | sunk cost | Phase 3 requires presenting at least 2 approaches with trade-offs before settling |
| "Brainstorm this idea but also implement it now" | scope creep | Key Rules: "Never write implementation code" — design doc only, plan mode for implementation |
