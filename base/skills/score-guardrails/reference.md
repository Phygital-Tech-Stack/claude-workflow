# Score Guardrails — Deep Reference

> **Rubric v2.1** — Stack-neutral. Aligned with OWASP Agentic Top 10 (2026), OpenSSF AI Code Assistant Guide, EU AI Act, NIST AI RMF, and Claude Code best practices.

## Scoring Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 0 | Absent | Not present at all |
| 1 | Minimal | Ad-hoc or token effort; exists but barely functional |
| 2 | Basic | Covers the happy path; gaps in edge cases |
| 3 | Solid | Covers common scenarios; documented; maintainable |
| 4 | Comprehensive | Covers edge cases; enforced automatically; well-integrated |
| 5 | Exemplary | Industry-leading; self-enforcing; battle-tested; documented for others to replicate |

## Tier Weights & Max Points

| Tier | Weight | Dimensions | Max Points |
|------|--------|-----------|------------|
| Foundation | x4 | D1-D5 | 100 |
| Enforcement | x3 | D6-D10 | 75 |
| Workflow | x2 | D11-D15 | 50 |
| Excellence | x1 | D16-D20 | 25 |
| **Total** | | **20** | **250** |

## Maturity Levels

| Range | Level | Description |
|-------|-------|-------------|
| 0-62 | Unguarded | AI is flying blind. High risk of inconsistent code, security holes, wasted effort. |
| 63-125 | Foundations | Basic guardrails in place. AI has context but limited enforcement. |
| 126-187 | Structured | Solid coverage. Automated enforcement catches most issues. |
| 188-250 | Elite | Best-in-class. Self-auditing, compression-resilient, fully orchestrated. |

---

## Dimension Scoring Criteria

### D1. Project Identity & Context Documentation (Foundation x4)

| Score | Criteria |
|-------|----------|
| 0 | No AI context file exists |
| 1 | Basic README with build/run instructions only |
| 2 | Root CLAUDE.md exists with tech stack and project structure |
| 3 | Includes conventions, architecture overview, and quick start commands |
| 4 | Adds domain-specific rules, anti-patterns, troubleshooting |
| 5 | Comprehensive: tech stack, architecture, conventions, domain glossary, workflow references — regularly maintained |

### D2. Layered Documentation Architecture (Foundation x4)

| Score | Criteria |
|-------|----------|
| 0 | No documentation beyond code comments |
| 1 | Single flat README or root CLAUDE.md |
| 2 | Root CLAUDE.md + one component-level guide |
| 3 | Root + component-level + feature-level documentation (3 layers) |
| 4 | 3+ layers + deep-reference blueprints in `.claude/blueprints/` |
| 5 | Full hierarchy with context-loading routing and refactoring guides |

### D3. Architecture Boundary Enforcement (Foundation x4)

| Score | Criteria |
|-------|----------|
| 0 | No boundaries; anything can import anything |
| 1 | Boundaries described but not enforced |
| 2 | Project structure implies boundaries |
| 3 | Lint rules enforce boundaries + documented import ordering |
| 4 | Lint-enforced + interfaces + documented dependency rules |
| 5 | Lint-enforced + hooks checking imports + dependency graph + cross-layer checklists |

### D4. Domain Terminology & Naming Standards (Foundation x4)

| Score | Criteria |
|-------|----------|
| 0 | No glossary; inconsistent naming |
| 1 | Informal conventions (team knowledge) |
| 2 | Naming conventions documented for one category |
| 3 | Conventions for all categories with examples |
| 4 | Full domain glossary + naming rules + terminology table |
| 5 | Glossary + rules + examples + coding-conventions blueprint + enforcement hook |

### D5. Code Style & Complexity Limits (Foundation x4)

| Score | Criteria |
|-------|----------|
| 0 | No limits; files grow unbounded |
| 1 | Linter configured but no file/function size rules |
| 2 | Formatter + lint rules |
| 3 | Formatter + lint + documented limits and extraction rules |
| 4 | Documented soft/hard limits per file type + proven refactoring results |
| 5 | Per-file-type limits + hook-enforced + extraction rules + documented in blueprint |

### D6. PreToolUse Guard Hooks (Enforcement x3)

| Score | Criteria |
|-------|----------|
| 0 | No PreToolUse hooks |
| 1 | 1 advisory hook (e.g., env warning) |
| 2 | 2-3 hooks including at least one enforcing guard (blocker or steering with downstream validation) |
| 3 | Covers secrets, critical files, and quick-fix detection |
| 4 | Adds prompt injection detection + stack-specific guards |
| 5 | Full coverage + documented in WORKFLOW.md + tested + maintained |

### D7. PostToolUse Validation Hooks (Enforcement x3)

| Score | Criteria |
|-------|----------|
| 0 | No PostToolUse hooks |
| 1 | Session file tracker only |
| 2 | Tracker + one validator (format or lint) |
| 3 | Tracker + format + lint + test reminder |
| 4 | Full linter suite + file size enforcement + import checking |
| 5 | Complete suite + auto-fix where safe + documented + benchmarked |

### D8. Commit Pipeline Integrity (Enforcement x3)

| Score | Criteria |
|-------|----------|
| 0 | No commit controls; `git commit` directly |
| 1 | Conventional commit format suggested |
| 2 | `/commit` skill exists with basic staging |
| 3 | `/commit` with lattice gate + code review + session tracking |
| 4 | Hard gate: `/validate-change` required before commit |
| 5 | Full pipeline: docs check + lattice gate + review + progress + tracking + verified |

### D9. Security Scanning Automation (Enforcement x3)

| Score | Criteria |
|-------|----------|
| 0 | No security scanning |
| 1 | Manual `grep` for secrets |
| 2 | Gitleaks or equivalent configured |
| 3 | `/security` skill with scan/deps/owasp subcommands |
| 4 | Integrated into `/validate-change` Layer 3 + CI |
| 5 | Full pipeline + OWASP ASI mapping + dependency SBOM + CI enforcement |

### D10. Agent Boundary Enforcement (Enforcement x3)

| Score | Criteria |
|-------|----------|
| 0 | No agents defined |
| 1 | Agents exist but no boundaries |
| 2 | `allowed-tools` in agent frontmatter |
| 3 | Tool restrictions + file ownership + documented boundaries |
| 4 | OWASP ASI07 mitigations + SubagentStart hook |
| 5 | Full ASI07 compliance + read-only review agents + tested escalation matrix |

### D11. TDD Workflow Integration (Workflow x2)

| Score | Criteria |
|-------|----------|
| 0 | No TDD workflow |
| 1 | Tests exist but written after implementation |
| 2 | `/tdd` skill exists with RED-GREEN-REFACTOR |
| 3 | TDD integrated into feature workflow + acceptance criteria |
| 4 | TDD guard hook prevents code-first + test quality standards |
| 5 | Full TDD pipeline + pressure tested + documented test patterns |

### D12. Validation Lattice Completeness (Workflow x2)

| Score | Criteria |
|-------|----------|
| 0 | No validation pipeline |
| 1 | Manual testing only |
| 2 | `/validate-change` exists with basic checks |
| 3 | 5-layer lattice (deterministic → semantic → security → agentic → human) |
| 4 | Auto-quick detection + severity tiers + cross-boundary trace |
| 5 | Full lattice + override documentation + examples + troubleshooting guide |

### D13. Session Continuity System (Workflow x2)

| Score | Criteria |
|-------|----------|
| 0 | No session state persistence |
| 1 | Manual notes between sessions |
| 2 | SessionStart hook injects git context |
| 3 | Progress files + session file tracking + context injection |
| 4 | Full lifecycle: start → track → compact → progress → cleanup |
| 5 | Compression-resilient + decision log + agent memory + plan progress |

### D14. Brainstorm-to-Implementation Pipeline (Workflow x2)

| Score | Criteria |
|-------|----------|
| 0 | Features implemented ad-hoc |
| 1 | Informal design discussions |
| 2 | `/brainstorm` skill exists |
| 3 | Brainstorm → design doc → plan mode → implementation |
| 4 | Design doc template + progress tracking + plan archival |
| 5 | Full pipeline + handoff protocol + validated incrementally + documented |

### D15. Documentation Drift Detection (Workflow x2)

| Score | Criteria |
|-------|----------|
| 0 | No drift detection |
| 1 | Manual review of docs |
| 2 | `/ai-guardrails-audit` skill exists |
| 3 | Diff-based scoping + 7 deterministic checks |
| 4 | Team mode with parallel reviewers + auto-fix |
| 5 | Full audit + CI integration + scheduled checks + fix mode |

### D16. Guardrail Self-Scoring (Excellence x1)

| Score | Criteria |
|-------|----------|
| 0 | No self-assessment |
| 1 | Informal assessment |
| 2 | `/score-guardrails` skill exists |
| 3 | 20-dimension rubric with weighted tiers |
| 4 | Evidence-based scoring + anti-inflation rules |
| 5 | Full rubric + standards alignment + testing provenance |

### D17. Skill Quality Standards (Excellence x1)

| Score | Criteria |
|-------|----------|
| 0 | No skill quality standards |
| 1 | Skills exist but inconsistent quality |
| 2 | `/writing-skills` skill exists |
| 3 | 7-dimension audit rubric + TDD creation process |
| 4 | Token budgets + pressure testing + scoring bands |
| 5 | Full quality system + audit-all mode + documented anti-patterns |

### D18. Workflow Sync Management (Excellence x1)

| Score | Criteria |
|-------|----------|
| 0 | No workflow management |
| 1 | Manual copy between projects |
| 2 | Master workflow repo exists |
| 3 | Init + sync + diff tooling |
| 4 | CI drift detection + auto-PR on drift |
| 5 | Full lifecycle: init → sync → diff → promote → CI + versioned |

### D19. Regulatory Compliance Artifacts (Excellence x1)

| Score | Criteria |
|-------|----------|
| 0 | No compliance artifacts |
| 1 | Co-Authored-By on some commits |
| 2 | Consistent Co-Authored-By + decision log |
| 3 | Full audit trail: decisions + progress + session tracking |
| 4 | OWASP ASI mapping + dependency SBOM + attribution |
| 5 | EU AI Act alignment + NIST RMF mapping + reproducible audit trail |

### D20. Cross-Project Consistency (Excellence x1)

| Score | Criteria |
|-------|----------|
| 0 | Each project has different workflow |
| 1 | Informal shared conventions |
| 2 | Shared skill/hook files (manual copy) |
| 3 | Master workflow with stack overlays |
| 4 | Automated sync + drift detection across projects |
| 5 | Full ecosystem: master repo + stacks + CI + adoption across all projects |

---

## Score Sheet Template

```
## Guardrail Score: [PROJECT NAME]

| # | Dimension | Tier | Score | Evidence |
|---|-----------|------|-------|----------|
| D1 | Project Identity | Foundation x4 | X/5 | [1-line evidence] |
| D2 | Layered Docs | Foundation x4 | X/5 | ... |
| D3 | Architecture Boundaries | Foundation x4 | X/5 | ... |
| D4 | Domain Terminology | Foundation x4 | X/5 | ... |
| D5 | Code Style Limits | Foundation x4 | X/5 | ... |
| D6 | PreToolUse Guards | Enforcement x3 | X/5 | ... |
| D7 | PostToolUse Hooks | Enforcement x3 | X/5 | ... |
| D8 | Commit Pipeline | Enforcement x3 | X/5 | ... |
| D9 | Security Scanning | Enforcement x3 | X/5 | ... |
| D10 | Agent Boundaries | Enforcement x3 | X/5 | ... |
| D11 | TDD Integration | Workflow x2 | X/5 | ... |
| D12 | Validation Lattice | Workflow x2 | X/5 | ... |
| D13 | Session Continuity | Workflow x2 | X/5 | ... |
| D14 | Brainstorm Pipeline | Workflow x2 | X/5 | ... |
| D15 | Drift Detection | Workflow x2 | X/5 | ... |
| D16 | Self-Scoring | Excellence x1 | X/5 | ... |
| D17 | Skill Quality | Excellence x1 | X/5 | ... |
| D18 | Workflow Sync | Excellence x1 | X/5 | ... |
| D19 | Regulatory Compliance | Excellence x1 | X/5 | ... |
| D20 | Cross-Project | Excellence x1 | X/5 | ... |

**Weighted Total**: XXX / 250
**Maturity Level**: [Unguarded | Foundations | Structured | Elite]

### Top Gaps (max 3)
1. [Highest impact gap]
2. [Second gap]
3. [Third gap]
```
