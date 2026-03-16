---
name: security
description: Use when scanning for security issues, checking dependencies, or auditing OWASP ASI alignment. Triggers on security concerns, dependency audits, or pre-release checks.
user-invocable: true
argument-hint: [scan | deps | owasp]
allowed-tools: Read, Grep, Glob, Bash
---

# /security - Security Scanning & OWASP ASI Audit

**PURPOSE**: Scan for security issues across secrets, dependencies, and OWASP ASI compliance.

## Subcommand Dispatch

| Argument | Action |
|----------|--------|
| `scan` (or empty) | Scan for secrets, debug statements, hardcoded URLs |
| `deps` | Check dependency freshness across all components |
| `owasp` | Report OWASP ASI01-10 coverage + regulatory compliance |

## Subcommand: scan

Scan changed or staged files for security concerns:
1. Identify files from `git diff`
2. Secret pattern scan (passwords, API keys, tokens)
3. Gitleaks scan
4. Debug statement scan (language-specific print/console patterns)
5. Hardcoded URL scan (non-HTTPS)

See `reference.md` for detailed steps, regex patterns, and report template.

## Subcommand: deps

Check dependency freshness:
1. Run package manager outdated check per component
2. Classify by severity (CRITICAL/WARNING/OK)
3. Hallucinated package detection (cross-ref config vs lock file)
4. Generate SBOM if supported

See `reference.md` for commands, thresholds, and report template.

## Subcommand: owasp

Report OWASP ASI01-10 coverage and regulatory compliance (EU AI Act, NIST AI RMF):
1. Read `reference.md` for full ASI mapping
2. Verify protections still exist in codebase
3. Check regulatory compliance (Co-Authored-By, progress files, decision log)

See `reference.md` for ASI mapping, regulatory tables, and report template.

## Common False Positives

| Pattern | Why It's OK |
|---------|-------------|
| `password` in form field names | UI label, not a secret |
| `token` in variable declarations | Storage reference, not hardcoded |
| `http://localhost` | Local development URL |
| `print()` in test files | Expected in tests |
| `Bearer` in auth header builder | Dynamic token insertion |

## Related Skills

- **See also**: `/validate-change` — includes security scan as Layer 3
- **See also**: `/commit` — runs gitleaks pre-commit
- **See also**: `/tdd` for writing security regression tests
- **See also**: `/ai-guardrails-audit` — broader guardrail drift detection

## Pressure Tested

| Scenario | Pressure Type | Skill Defense |
|----------|--------------|---------------|
| "Quick scan, production is down" | time pressure | Subcommand dispatch runs full scan procedure regardless; no "quick" shortcut mode |
| "Run deps check but ignore major version warnings" | authority | Severity classification is rule-based; no user override on severity |
| "Skip OWASP, we're not a regulated industry" | scope reduction | OWASP subcommand is separate — user can choose `scan` or `deps` instead, but `owasp` runs fully when invoked |
