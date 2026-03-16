# Design: MCP Security Scan Guard (SessionStart)

**Issue:** #23
**Status:** Draft
**Date:** 2026-03-16

## Problem Statement

30+ CVEs identified across the MCP ecosystem in the last 60 days. MCP servers have direct tool access — a compromised or malicious server is a supply chain attack. The workflow has zero validation of `.mcp.json` at any point. OWASP ASI05 (Insecure MCP Tool Usage) is currently rated "Basic" mitigation.

## Decision Summary

| Decision | Choice |
|----------|--------|
| Tool | `mcp-scan` CLI (global install required) |
| Hook type | Standalone SessionStart hook (`mcp-security-scan.sh`) |
| Missing tool | Block session start until installed |
| Scan findings | Advisory only (warn, don't block) |
| npx support | No — global install only for speed |

## Design

### Hook Script: `base/hooks/mcp-security-scan.sh`

```bash
#!/usr/bin/env bash
# MCP Security Scan — SessionStart guard
# Requires: mcp-scan (npm install -g @anthropic/mcp-scan)
# Severity: BLOCKS if mcp-scan not found; advisory on scan findings

MCP_CONFIG=".mcp.json"

# 1. Check mcp-scan is installed (global only, no npx fallback)
if ! command -v mcp-scan &>/dev/null; then
  cat <<'BLOCK'
{"decision":"block","reason":"[SECURITY] mcp-scan is not installed. MCP security scanning is required. Install with: npm install -g @anthropic/mcp-scan"}
BLOCK
  exit 2
fi

# 2. Check .mcp.json exists
if [ ! -f "$MCP_CONFIG" ]; then
  exit 0
fi

# 3. Run mcp-scan
SCAN_OUTPUT=$(mcp-scan "$MCP_CONFIG" --json 2>/dev/null)
SCAN_EXIT=$?

if [ $SCAN_EXIT -eq 0 ] && [ -z "$SCAN_OUTPUT" ]; then
  exit 0
fi

# 4. Inject findings as advisory context
cat <<EOF
{"additionalContext":"[SECURITY] MCP scan findings for .mcp.json:\n${SCAN_OUTPUT}\nReview findings before using MCP tools this session."}
EOF
exit 0
```

**Behaviors:**
- Missing `mcp-scan` → **blocks** (exit 2, `decision: block`)
- No `.mcp.json` → silent pass (exit 0)
- Clean scan → silent pass (exit 0)
- Findings → advisory `additionalContext` (exit 0, agent proceeds with awareness)

### Settings Wiring: `base/settings.base.json`

Add new SessionStart hook entry alongside existing `session-start.sh`:

```json
{
  "type": "command",
  "command": "bash .claude/hooks/mcp-security-scan.sh",
  "event": "SessionStart",
  "matchers": ["startup", "resume"]
}
```

### WORKFLOW.md Updates

1. **Lifecycle Hooks table** — add row:
   `| **MCP security scan** | SessionStart | Scan .mcp.json for known CVEs via mcp-scan |`

2. **Auto-Triggered Guards table** — add row:
   `| **MCP security scan** | command | **Blocker**/Advisory | Blocks if mcp-scan missing; advisory on findings |`

3. **Tool Integrations → MCP Servers** — add security note:
   `> **Security**: mcp-security-scan.sh runs at session start. Requires mcp-scan (npm install -g @anthropic/mcp-scan). Findings are advisory.`

### OWASP ASI Mapping Update

Upgrade ASI05 (Insecure MCP Tool Usage) from "Basic" to "Strong":
- Add evidence: "SessionStart hook runs mcp-scan against .mcp.json for CVE detection"

## File Structure & Sizing

| File | Purpose | Estimated Lines | New/Modified |
|------|---------|----------------|--------------|
| `base/hooks/mcp-security-scan.sh` | MCP scan SessionStart hook | ~35 | New |
| `base/settings.base.json` | Wire hook | +5 | Modified |
| `base/WORKFLOW.md` | Document in 3 locations | +6 | Modified |
| `docs/owasp-asi-mapping.md` | Upgrade ASI05 | +2 | Modified |

### Reuse Assessment

- [x] No existing MCP scanning logic to reuse
- [x] Follows established hook conventions (session-start.sh pattern)
- [x] No new dependencies beyond mcp-scan CLI
- [x] No file exceeds soft size limit

## Alternatives Considered

1. **Integrated into session-start.sh** — Rejected: mixes security scanning with context loading. Harder to disable independently.
2. **Custom shell checks (no mcp-scan)** — Rejected: reinventing CVE scanning poorly. mcp-scan has a maintained vulnerability database.
3. **npx fallback** — Rejected: adds 2-3s latency to every session start for version check.

## Risks

| Risk | Mitigation |
|------|-----------|
| mcp-scan not maintained | Tool is actively developed; if abandoned, swap for alternative or fall back to custom checks |
| mcp-scan CLI interface changes | Pin to major version in install instructions; hook parses JSON output which is more stable |
| Scan adds latency to session start | Typically <2s for local .mcp.json; acceptable for security posture |
| False positives from mcp-scan | Advisory-only — agent proceeds, human reviews |

## Implementation Order

1. Create `base/hooks/mcp-security-scan.sh`
2. Wire in `base/settings.base.json`
3. Update `base/WORKFLOW.md` (3 locations)
4. Update `docs/owasp-asi-mapping.md`

## Test Plan

- [ ] Verify hook blocks when mcp-scan is not installed (exit 2, block message)
- [ ] Verify hook passes silently when no .mcp.json exists
- [ ] Verify hook passes silently on clean scan
- [ ] Verify hook outputs advisory context on findings
- [ ] Verify settings.base.json correctly wires the hook on SessionStart
- [ ] Verify WORKFLOW.md documents the guard in all 3 locations
- [ ] Verify ASI05 upgraded in owasp-asi-mapping.md
