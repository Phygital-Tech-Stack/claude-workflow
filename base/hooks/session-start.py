import json, os, glob, re, subprocess, sys, time

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

# Persist session_id as env var for Bash commands (used by /commit)
session_id = re.sub(r'[^a-zA-Z0-9_\-]', '', data.get('session_id', ''))
env_file = os.environ.get('CLAUDE_ENV_FILE', '')
if session_id and env_file:
    with open(env_file, 'a') as f:
        f.write(f'export CLAUDE_SESSION_ID="{session_id}"\n')

# Clean up stale session tracking files (older than 7 days)
claude_dir = ".claude"
if os.path.isdir(claude_dir):
    now = time.time()
    for sf in glob.glob(os.path.join(claude_dir, "session-files-*.txt")):
        try:
            if now - os.path.getmtime(sf) > 7 * 86400:
                os.remove(sf)
        except Exception:
            pass

parts = []

# 1. Check docs/plans/3-in-progress/ for active plan progress files
plans_dir = "docs/plans/3-in-progress"
for f in sorted(glob.glob(os.path.join(plans_dir, "*-progress.md"))):
    try:
        with open(f) as fh:
            content = fh.read()
        if "IN PROGRESS" not in content:
            continue
        name = os.path.basename(f).replace("-progress.md", "").lstrip("0123456789-")
        in_section = False
        items = []
        for line in content.split("\n"):
            if "## Next Session Should" in line:
                in_section = True
                continue
            if in_section and line.startswith("##"):
                break
            if in_section and line.strip():
                items.append(line.strip())
        if items:
            parts.append(f"[Active Plan] {name}: {'; '.join(items[:5])}")
    except Exception:
        continue

# 2. Check .claude/progress/ for most recent session progress
progress_dir = os.path.join(claude_dir, "progress")
progress_files = sorted(glob.glob(os.path.join(progress_dir, "*.md")))
progress_files = [pf for pf in progress_files if not pf.endswith(".gitkeep")]
if progress_files:
    latest = progress_files[-1]
    try:
        with open(latest) as fh:
            content = fh.read()
        in_section = False
        items = []
        for line in content.split("\n"):
            if "## Next Session Should" in line:
                in_section = True
                continue
            if in_section and line.startswith("##"):
                break
            if in_section and line.strip():
                items.append(line.strip())
        if items:
            parts.append(f"[Last Session] {'; '.join(items[:5])}")
    except Exception:
        pass

# 3. Git context
try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True, timeout=1
    ).strip()
except Exception:
    branch = "unknown"

try:
    commits = subprocess.check_output(
        ["git", "log", "--oneline", "-3"], text=True, timeout=1
    ).strip().replace("\n", " | ")
except Exception:
    commits = ""

ctx = f"Branch: {branch}"
if commits:
    ctx += f"\nRecent: {commits}"
if parts:
    ctx += "\n" + "\n".join(parts)

print(json.dumps({"additionalContext": ctx}))
