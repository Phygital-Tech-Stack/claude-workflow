import json, os, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

# Check for context token data in environment or stdin
tokens_used = int(os.environ.get("CLAUDE_CONTEXT_TOKENS_USED", 0))
token_limit = int(os.environ.get("CLAUDE_CONTEXT_WINDOW", 0))

# Also check stdin data for context info
if not tokens_used:
    tokens_used = data.get("context_tokens_used", 0)
if not token_limit:
    token_limit = data.get("context_window", 0)

if not tokens_used or not token_limit:
    sys.exit(0)

try:
    pct = (int(tokens_used) / int(token_limit)) * 100
except (ValueError, ZeroDivisionError):
    sys.exit(0)

if pct >= 90:
    print(json.dumps({"additionalContext":
        f"[Context] {pct:.0f}% used — CRITICAL. /compact now before any further work. "
        f"Do not commit from this state."
    }))
elif pct >= 80:
    print(json.dumps({"additionalContext":
        f"[Context] {pct:.0f}% used — HIGH. /compact before running /validate-change "
        f"or results may degrade."
    }))
elif pct >= 60:
    print(json.dumps({"additionalContext":
        f"[Context] {pct:.0f}% used. Consider /compact before starting a new feature."
    }))

sys.exit(0)
