import json, os, glob, subprocess, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

parts = []

# 1. Git context (branch + last commit)
try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True, timeout=1
    ).strip()
except Exception:
    branch = ""

try:
    last_commit = subprocess.check_output(
        ["git", "log", "--oneline", "-1"], text=True, timeout=1
    ).strip()
except Exception:
    last_commit = ""

if branch:
    ctx = f"Branch: {branch}"
    if last_commit:
        ctx += f" ({last_commit})"
    parts.append(ctx)

# 2. Check for active progress files
claude_dir = ".claude"
progress_dir = os.path.join(claude_dir, "progress")
progress_files = sorted(glob.glob(os.path.join(progress_dir, "*.md")))
progress_files = [pf for pf in progress_files if not pf.endswith(".gitkeep")]
if progress_files:
    latest = progress_files[-1]
    name = os.path.basename(latest).replace(".md", "")
    parts.append(f"[Active Progress] {name} — load with: Read {latest}")

# 3. Check for dangerous patterns in user prompt
prompt_text = data.get("prompt", "").lower()
dangerous = {
    "delete all": "bulk deletion",
    "drop table": "table drop",
    "drop database": "database drop",
    "drop schema": "schema drop",
    "truncate table": "table truncation",
    "rm -rf /": "recursive root delete",
    "rm -rf ~": "recursive home delete",
    "format c:": "disk format",
    "git push --force main": "force-push to main",
    "git push --force master": "force-push to master",
    "reset --hard": "hard reset",
}
matched = [desc for pat, desc in dangerous.items() if pat in prompt_text]
if matched:
    parts.append(f"[WARN] Dangerous pattern(s) detected: {', '.join(matched)}. Proceed with caution.")

if parts:
    print(json.dumps({"additionalContext": "\n".join(parts)}))

sys.exit(0)
