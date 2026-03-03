#!/usr/bin/env bash
# SubagentStart hook — inject project rules and agent memory into specialist agents

exec python3 - <<'PYTHON'
import json, sys, os

data = json.load(sys.stdin)
agent_name = data.get('agent_name', '')

# Load project-specific rules
rules = ""
rules_file = os.path.join(".claude", "project-rules.txt")
if os.path.exists(rules_file):
    try:
        with open(rules_file) as f:
            rules = f.read().strip()
    except Exception:
        pass

if not rules:
    rules = "No project-specific rules file found at .claude/project-rules.txt"

# Load agent-specific memory if available
memory = ""
memory_file = os.path.join(".claude", "agent-memory", agent_name, "MEMORY.md")
if os.path.exists(memory_file):
    try:
        with open(memory_file) as f:
            memory = "\n\n--- Agent Memory ---\n" + f.read()
    except Exception:
        pass

print(json.dumps({"additionalContext": rules + memory}))
PYTHON
