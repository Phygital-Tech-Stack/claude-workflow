import json, os, shutil, subprocess, sys

# Consume stdin (Claude Code sends hook context via stdin)
try:
    json.load(sys.stdin)
except Exception:
    pass

MCP_CONFIG = ".mcp.json"

# 1. Check mcp-scan is installed
if not shutil.which("mcp-scan"):
    print(json.dumps({
        "additionalContext": "[SECURITY] mcp-scan is not installed. Install with: pip install mcp-scan"
    }))
    sys.exit(0)

# 2. Check .mcp.json exists
if not os.path.isfile(MCP_CONFIG):
    sys.exit(0)

# 3. Run mcp-scan
try:
    result = subprocess.run(
        ["mcp-scan", MCP_CONFIG, "--json"],
        capture_output=True, text=True, timeout=30
    )
    scan_output = result.stdout
    scan_exit = result.returncode
except Exception:
    sys.exit(0)

# 4. Clean scan — no findings
if scan_exit == 0:
    try:
        data = json.loads(scan_output)
        findings = data if isinstance(data, list) else data.get("findings", data.get("vulnerabilities", []))
        finding_count = len(findings) if isinstance(findings, list) else 0
    except Exception:
        finding_count = 0

    if finding_count == 0:
        sys.exit(0)

# 5. Findings detected — inject as advisory context
escaped = json.dumps(scan_output)[1:-1]  # Strip surrounding quotes
print(json.dumps({
    "additionalContext": f"[SECURITY] MCP scan findings for .mcp.json:\n{escaped}\nReview findings before using MCP tools this session."
}))
sys.exit(0)
