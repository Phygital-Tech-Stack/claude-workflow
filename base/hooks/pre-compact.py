import json, os, sys
from datetime import datetime

log_file = os.path.join(".claude", "compaction.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

timestamp = datetime.now().isoformat()

# Extract token usage if available
tokens_used = data.get("context_tokens_used", os.environ.get("CLAUDE_CONTEXT_TOKENS_USED", ""))
token_limit = data.get("context_window", os.environ.get("CLAUDE_CONTEXT_WINDOW", ""))
token_info = ""
if tokens_used and token_limit:
    try:
        pct = (int(tokens_used) / int(token_limit)) * 100
        token_info = f" context={pct:.0f}%"
    except (ValueError, ZeroDivisionError):
        pass

with open(log_file, "a") as f:
    f.write(f"[{timestamp}]{token_info} Compaction: {json.dumps(data)}\n")

sys.exit(0)
