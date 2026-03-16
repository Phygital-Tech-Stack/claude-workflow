import json, sys, os, importlib.util

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input", {})
cmd = tool_input.get("command", "")
stderr = data.get("stderr", "")
stdout = data.get("stdout", "")
output = f"{stdout}\n{stderr}".lower()

suggestions = []

# Generic git failures (all stacks)
if "git" in cmd:
    if "conflict" in output and "merge" in output:
        suggestions.append("Merge conflict — resolve conflicts, then git add and git commit")
    elif "nothing to commit" in output:
        suggestions.append("No changes to commit — check git status for unstaged changes")
    elif "rejected" in output and "push" in cmd:
        suggestions.append("Push rejected — pull remote changes first with git pull --rebase")

# Load stack-specific pattern files
patterns_dir = os.path.join(".claude", "hooks", "failure-patterns")
if os.path.isdir(patterns_dir):
    for pf in sorted(os.listdir(patterns_dir)):
        if not pf.endswith(".py"):
            continue
        pf_path = os.path.join(patterns_dir, pf)
        try:
            spec = importlib.util.spec_from_file_location(pf.replace(".py", ""), pf_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "match"):
                result = mod.match(cmd, output)
                if result:
                    suggestions.extend(result if isinstance(result, list) else [result])
        except Exception:
            pass

if suggestions:
    print(json.dumps({"additionalContext": "[Recovery] " + "; ".join(suggestions)}))

sys.exit(0)
