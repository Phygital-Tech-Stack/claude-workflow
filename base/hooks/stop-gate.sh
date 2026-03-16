#!/usr/bin/env bash
# Stop hook — remind to validate if source files were modified this session
# Advisory only (exit 0) — does not block stopping

exec python3 <(cat <<'PYTHON'
import json, os, glob, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

sid = data.get("session_id", "unknown")
session_file = os.path.join(".claude", f"session-files-{sid}.txt")
if not os.path.exists(session_file):
    sys.exit(0)

with open(session_file) as f:
    files = [l.strip() for l in f if l.strip()]

# Check for code file modifications
ext_str = os.environ.get("WORKFLOW_CODE_EXTENSIONS", ".ts,.tsx,.py,.dart,.cs")
extensions = tuple(e.strip() for e in ext_str.split(","))
exclude = (".g.dart", ".freezed.dart", ".generated.ts")
code_files = [fn for fn in files if fn.endswith(extensions) and not fn.endswith(exclude)]

if not code_files:
    sys.exit(0)

# Check if /validate-change was likely run (look for lattice verdict markers)
messages = []
validated = False

# Check for validation marker in progress files
claude_dir = ".claude"
progress_files = sorted(glob.glob(os.path.join(claude_dir, "progress", "*.md")))
for pf in progress_files[-2:]:  # Check last 2 progress files
    try:
        with open(pf) as fh:
            content = fh.read()
        if "validate-change" in content.lower() or "lattice" in content.lower():
            validated = True
            break
    except Exception:
        continue

if not validated:
    messages.append(
        f"[Stop Gate] {len(code_files)} code file(s) modified this session. "
        f"Consider running /validate-change before ending."
    )

# Check for uncommitted changes
try:
    import subprocess
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], text=True, timeout=2
    ).strip()
    if status:
        modified_count = len(status.split("\n"))
        messages.append(
            f"[Stop Gate] {modified_count} uncommitted change(s). "
            f"Consider running /commit before ending."
        )
except Exception:
    pass

if messages:
    print(json.dumps({"additionalContext": "\n".join(messages)}))

sys.exit(0)
PYTHON
)
