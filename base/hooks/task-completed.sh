#!/usr/bin/env bash
# TaskCompleted hook — remind to validate when code files were modified
# Non-blocking (exit 0) — provides context, does not gate completion

exec python3 <(cat <<'PYTHON'
import json, os, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

sid = data.get('session_id', 'unknown')
session_file = os.path.join(".claude", f"session-files-{sid}.txt")
if not os.path.exists(session_file):
    sys.exit(0)

with open(session_file) as f:
    files = [l.strip() for l in f if l.strip()]

# Read code extensions from env or use defaults
ext_str = os.environ.get("WORKFLOW_CODE_EXTENSIONS", ".ts,.tsx,.py,.dart,.cs")
extensions = tuple(e.strip() for e in ext_str.split(","))

# Exclude generated files
exclude = (".g.dart", ".freezed.dart", ".generated.ts")
code_files = [f for f in files if f.endswith(extensions) and not f.endswith(exclude)]

if code_files:
    print(json.dumps({
        "additionalContext": f"[Quality] {len(code_files)} code file(s) modified this session. Run /validate-change before /commit."
    }))

sys.exit(0)
PYTHON
)
