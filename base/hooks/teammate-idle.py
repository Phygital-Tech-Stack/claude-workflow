import json, os, sys, glob

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

# Check for active plans
plans_dir = "docs/plans/3-in-progress"
active = []
for f in glob.glob(os.path.join(plans_dir, "*-progress.md")):
    try:
        with open(f) as fh:
            content = fh.read()
        if "IN PROGRESS" in content:
            unchecked = content.count("- [ ]")
            if unchecked > 0:
                name = os.path.basename(f).replace("-progress.md", "")
                active.append(f"{name} ({unchecked} steps remaining)")
    except Exception:
        pass

if active:
    print(json.dumps({
        "additionalContext": "[Idle] Active plans with remaining work: " + "; ".join(active) + ". Check TaskList for available tasks."
    }))

sys.exit(0)
