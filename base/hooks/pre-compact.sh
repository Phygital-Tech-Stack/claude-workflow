#!/usr/bin/env bash
# PreCompact hook — log compaction events for debugging
# Read-only observer: cannot modify Claude behavior, just records the event

exec python3 <(cat <<'PYTHON'
import json, os, sys
from datetime import datetime

log_file = os.path.join(".claude", "compaction.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

timestamp = datetime.now().isoformat()
with open(log_file, "a") as f:
    f.write(f"[{timestamp}] Compaction: {json.dumps(data)}\n")

sys.exit(0)
PYTHON
)
