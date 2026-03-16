import json, os, glob, sys, subprocess
from datetime import datetime

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

sid = data.get("session_id", "unknown")
session_file = os.path.join(".claude", f"session-files-{sid}.txt")

# Count modified code files
code_files = []
if os.path.exists(session_file):
    with open(session_file) as f:
        files = [line.strip() for line in f if line.strip()]
    ext_str = os.environ.get("WORKFLOW_CODE_EXTENSIONS", ".ts,.tsx,.py,.dart,.cs")
    extensions = tuple(e.strip() for e in ext_str.split(","))
    exclude = (".g.dart", ".freezed.dart", ".generated.ts")
    code_files = [f for f in files if f.endswith(extensions) and not f.endswith(exclude)]

# Check for uncommitted changes
uncommitted = 0
try:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], text=True, timeout=2
    ).strip()
    if status:
        uncommitted = len(status.split("\n"))
except Exception:
    pass

# Build warnings
messages = []

if code_files:
    # Check if /validate-change was run
    validated = False
    progress_files = sorted(glob.glob(os.path.join(".claude", "progress", "*.md")))
    for pf in progress_files[-2:]:
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
            f"[STEER] {len(code_files)} code file(s) modified this session. "
            f"Consider running /validate-change before ending."
        )

if uncommitted:
    messages.append(
        f"[STEER] {uncommitted} uncommitted change(s). "
        f"Consider running /commit before ending."
    )

# Log session metrics
try:
    metrics_file = os.path.join(".claude", "session-metrics.log")
    entry = json.dumps({
        "timestamp": datetime.now().isoformat(),
        "session_id": sid,
        "code_files_modified": len(code_files),
        "uncommitted_changes": uncommitted
    })
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    with open(metrics_file, "a") as f:
        f.write(entry + "\n")
except Exception:
    pass

if messages:
    print(json.dumps({"additionalContext": "\n".join(messages)}))

sys.exit(0)
