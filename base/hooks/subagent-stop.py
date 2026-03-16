import json, sys, re

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

# Extract subagent info
agent_name = data.get("agent_name", data.get("tool_name", "unknown"))
output = data.get("output", data.get("stdout", ""))
stderr = data.get("stderr", "")

warnings = []

# Check for empty output
if not output or len(output.strip()) < 10:
    warnings.append(
        f"[STEER] Subagent '{agent_name}' returned empty or very short output. "
        f"Review before proceeding."
    )

# Check for failure patterns in output or stderr
combined = (output or "") + (stderr or "")
failure_patterns = [
    r"Traceback \(most recent call last\)",
    r"(?i)error:\s",
    r"(?i)timed?\s*out",
    r"(?i)I couldn'?t",
    r"(?i)I was unable to",
    r"(?i)failed to complete",
]

for pattern in failure_patterns:
    if re.search(pattern, combined):
        warnings.append(
            f"[STEER] Subagent '{agent_name}' output contains failure indicators. "
            f"Verify the result is usable."
        )
        break

if warnings:
    print(json.dumps({"additionalContext": "\n".join(warnings)}))

sys.exit(0)
