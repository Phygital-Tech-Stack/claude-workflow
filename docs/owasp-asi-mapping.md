# OWASP ASI (Agentic Security Issues) Mapping

> Maps each OWASP Agentic Security Issue to specific workflow mitigations.
> Last updated: 2026-03-10 | Workflow version: 1.4.1

## Risk Mapping

| # | ASI Risk | Severity | Mitigation | Evidence |
|---|----------|----------|------------|----------|
| ASI01 | Prompt Injection | Critical | `prompt-injection.json` PreToolUse hook detects injection patterns in code being written. Advisory warning on match. | `base/guards/prompt-injection.json` |
| ASI02 | Insecure Output Handling | High | `/validate-change` Layer 1 (lint/typecheck) + Layer 3 (security scan) catch unsafe output patterns. PostToolUse hooks auto-format to prevent malformed output. | `.claude/skills/validate-change/`, stack PostToolUse hooks |
| ASI03 | Supply Chain Vulnerabilities | High | `/security deps` subcommand audits dependencies. Stack-specific lock files tracked. | `.claude/skills/security/` |
| ASI04 | Sensitive Information Disclosure | Critical | `env-secrets.json` PreToolUse hook warns on credential file edits. `/security scan` detects secrets in code. | `base/guards/env-secrets.json` |
| ASI05 | Insecure MCP Tool Usage | Medium | MCP servers configured per-stack via `.mcp.json.template`. Pharos and GitHub servers use token-based auth. `enabledMcpjsonServers` in settings controls which servers are active. SessionStart hook runs `mcp-scan` against `.mcp.json` for CVE detection. | `stacks/*/.mcp.json.template`, `base/hooks/mcp-security-scan.sh` |
| ASI06 | Excessive Agency | High | `scope-estimator.json` PreToolUse hook warns on high blast-radius changes (>5 files). `critical-file.json` guard warns on infrastructure file edits. Stop hook warns on unvalidated changes. | `base/guards/scope-estimator.json`, `base/guards/critical-file.json` |
| ASI07 | Agent Privilege Escalation | Critical | Each agent has `allowed-tools` frontmatter restricting tool access. Review agents (security-reviewer, planner, db-expert) are read-only. SubagentStart hook injects project rules — agents don't share mutable state. Agents communicate only through orchestrator. | `.claude/agents/*.md`, `.claude/hooks/subagent-start.sh` |
| ASI08 | Insufficient Logging & Monitoring | Medium | Session file tracking logs all modified files. `decisions.log` records architectural decisions. `compaction.log` tracks context events. Progress files maintain session state. | `.claude/session-files-*.txt`, `.claude/decisions.log`, `.claude/compaction.log` |
| ASI09 | Improper Error Handling | Medium | `PostToolUseFailure` hook pattern-matches errors and suggests recovery. Stack-specific `failure-patterns/` directories define known error patterns. | `.claude/hooks/post-failure.sh`, `stacks/*/failure-patterns/` |
| ASI10 | Misaligned Behaviors | High | `/brainstorm` enforces design-before-code workflow. `/validate-change` 5-layer lattice catches behavioral drift. `quick-fix-blocker.json` prevents hack/workaround markers. TDD workflow ensures tests precede implementation. | `.claude/skills/brainstorm/`, `.claude/skills/validate-change/`, `base/guards/quick-fix-blocker.json` |

## Coverage Summary

| Coverage Level | Risks | Count |
|---------------|-------|-------|
| Strong (automated enforcement) | ASI01, ASI04, ASI06, ASI07, ASI10 | 5 |
| Moderate (tooling available) | ASI02, ASI03, ASI05, ASI08, ASI09 | 5 |

## Gap Analysis

- **ASI03**: No automated SBOM generation. `/security deps` relies on manual invocation.
- **ASI05**: `mcp-scan` runs at session start for CVE detection. Remaining gap: no runtime tool-call validation beyond `allowed-tools`.
- **ASI08**: Logging is file-based with no centralized aggregation or alerting.

## Standards Cross-Reference

| Standard | Alignment |
|----------|-----------|
| OWASP Agentic Top 10 (2026) | Direct mapping above |
| OpenSSF AI Code Assistant Guide | Agent boundaries (ASI07), supply chain (ASI03), output handling (ASI02) |
| NIST AI RMF | Risk identification (this document), governance (WORKFLOW.md), monitoring (session tracking) |
| EU AI Act | Transparency (Co-Authored-By attribution), human oversight (`/validate-change` Layer 5), documentation (design docs, decision log) |
