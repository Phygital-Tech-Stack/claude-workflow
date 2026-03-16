#!/usr/bin/env bash
# SubagentStart hook — inject project rules and agent memory into specialist agents

exec python3 - <<'PYTHON'
import json, sys, os

import re
data = json.load(sys.stdin)
agent_name = re.sub(r'[^a-zA-Z0-9_-]', '', data.get('agent_name', ''))

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

# Load project auto-memory if available (supplementary, lower priority)
# Auto-memory dirs use sanitized cwd path as directory name
auto_mem = ""
auto_mem_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects")
if os.path.isdir(auto_mem_dir):
    cwd = os.getcwd()
    # Match current project by checking if cwd path is encoded in directory name
    cwd_slug = cwd.replace("/", "-").lstrip("-")
    for d in os.listdir(auto_mem_dir):
        if cwd_slug not in d and cwd.replace("/", "-") not in d:
            continue
        mem_path = os.path.join(auto_mem_dir, d, "memory", "MEMORY.md")
        if os.path.exists(mem_path):
            try:
                with open(mem_path) as f:
                    content = f.read().strip()
                if content:
                    auto_mem = "\n\n--- Auto-Memory (supplementary) ---\n" + content[:2000]
                    break
            except Exception:
                pass

print(json.dumps({"additionalContext": rules + memory + auto_mem}))
PYTHON
