# Changelog

## [1.2.0] - 2026-03-09

### Added
- UserPromptSubmit hook: injects git context, active progress, warns on dangerous patterns (#5)
- Stop hook: warns if code files modified but not validated or committed (#5)
- Context-check hook: warns at 60%/80%/90% context window thresholds (#8)
- Prompt and agent hook types for guards — compose_settings.py now supports all three types (#6)
- Scope-estimator guard (type: prompt) — warns on high blast radius changes (#6)
- Critical-file-agent guard (type: agent) — opt-in deep review for critical files (#6)
- MCP server templates per stack: pharos, context7, github (#7)
- merge_mcp_templates.py shared tool with unresolved token warnings (#7)
- CI/CD templates: GitHub Actions PR review, GitLab CI MR review (#9)
- init.sh --ci flag for CI template installation (#9)
- 6 new agent definitions: planner, backend-handler, frontend-handler, test-writer, security-reviewer, db-expert (#10)
- Agent orchestration pattern and parallel vs sequential guidance in WORKFLOW.md (#10)
- Visual verification workflow for flutter-dart with screenshot convention (#11)
- Auto-memory vs agent-memory policy documented in WORKFLOW.md (#12)
- Context Window Management section in WORKFLOW.md with compact thresholds (#8)
- CI/CD Integration section in WORKFLOW.md (#9)

### Changed
- critical-file guard converted from type: command to type: prompt (#6)
- compose_settings.py resolve_guard_refs() copies full hook dict instead of just command+timeout (#6)
- compose_settings.py merge_overrides() now deduplicates permissions lists (#6)
- compose_settings.py warns on missing PyYAML instead of silently skipping (#6)
- init.sh preserves existing workflow.overrides.yaml on re-init (#9)
- pre-compact.sh logs context token level at compaction time (#8)
- subagent-start.sh injects project-scoped auto-memory as supplementary context (#12)
- brainstorm skill: context budget note at >60% (#8)
- validate-change skill: quick mode recommendation at >70% context (#8)
- flutter-dart commands.yaml: added SCREENSHOT_COMMAND (#11)
- projects.json: added ci_enabled field per project (#9)
- Session Continuity diagram updated with UserPromptSubmit and Stop hooks (#5)

### Fixed
- sync.sh garbled echo/sed output line
- init.sh step numbering gap (3→5)

## [1.1.0] - 2026-03-03

### Added
- Overrides merge, agent discovery, and placeholder resolution in compose_settings.py
- Template variable resolution in sync.sh
- TDD ceremony distinction and WORKFLOW.md scaffolding improvements

## [1.0.0] - 2026-03-03

### Added
- Base workflow: WORKFLOW.md, 6 lifecycle hooks, 6 guard definitions
- Core skills: commit, validate-change, tdd, brainstorm, ai-guardrails-audit, score-guardrails, security, writing-skills, sync-workflow
- Code-reviewer agent template
- Blueprint templates: coding-conventions, testing-patterns
- Stack overlays: typescript-nestjs, flutter-dart, python-fastapi, csharp-dotnet
- Sync tooling: init.sh, sync.sh, diff.sh, promote.sh, compose_settings.py
- CI: release.yml, drift-check.yml, project template workflow
