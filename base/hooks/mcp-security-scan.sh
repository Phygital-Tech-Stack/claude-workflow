#!/usr/bin/env bash
# SessionStart hook — scan .mcp.json for security vulnerabilities
# Requires: mcp-scan (npm install -g @anthropic/mcp-scan)
# Blocks if mcp-scan not installed; advisory on scan findings

# Consume stdin (Claude Code sends hook context via stdin)
cat > /dev/null

MCP_CONFIG=".mcp.json"

# 1. Check mcp-scan is installed (global only, no npx fallback)
if ! command -v mcp-scan &>/dev/null; then
  echo '{"decision":"block","reason":"[SECURITY] mcp-scan is not installed. MCP security scanning is required. Install with: npm install -g @anthropic/mcp-scan"}'
  exit 2
fi

# 2. Check .mcp.json exists
if [ ! -f "$MCP_CONFIG" ]; then
  exit 0
fi

# 3. Run mcp-scan
SCAN_OUTPUT=$(mcp-scan "$MCP_CONFIG" --json 2>/dev/null)
SCAN_EXIT=$?

# 4. Clean scan — no findings
if [ $SCAN_EXIT -eq 0 ]; then
  FINDING_COUNT=$(echo "$SCAN_OUTPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    findings = data if isinstance(data, list) else data.get('findings', data.get('vulnerabilities', []))
    print(len(findings) if isinstance(findings, list) else 0)
except Exception:
    print(0)
" 2>/dev/null)

  if [ "$FINDING_COUNT" = "0" ] || [ -z "$FINDING_COUNT" ]; then
    exit 0
  fi
fi

# 5. Findings detected — inject as advisory context
# Escape the output for JSON embedding
ESCAPED_OUTPUT=$(echo "$SCAN_OUTPUT" | python3 -c "
import sys, json
raw = sys.stdin.read()
print(json.dumps(raw)[1:-1])
" 2>/dev/null)

echo "{\"additionalContext\":\"[SECURITY] MCP scan findings for .mcp.json:\\n${ESCAPED_OUTPUT}\\nReview findings before using MCP tools this session.\"}"
exit 0
