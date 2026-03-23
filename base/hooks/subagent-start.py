import json, sys, os, re

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)
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
# Use direct path construction instead of scanning ~/.claude/projects/
auto_mem = ""
cwd = os.getcwd()
cwd_slug = cwd.replace("/", "-").lstrip("-")
auto_mem_path = os.path.join(
    os.path.expanduser("~"), ".claude", "projects", cwd_slug, "memory", "MEMORY.md"
)
if os.path.exists(auto_mem_path):
    try:
        with open(auto_mem_path) as f:
            content = f.read().strip()
        if content:
            auto_mem = "\n\n--- Auto-Memory (supplementary) ---\n" + content[:2000]
    except Exception:
        pass

print(json.dumps({"additionalContext": rules + memory + auto_mem}))
