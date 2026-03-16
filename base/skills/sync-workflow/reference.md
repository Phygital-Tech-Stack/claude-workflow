# Sync Workflow - Deep Reference

## Step 2: Discover Latest Version & Fetch Master

### Discover versions

```bash
MASTER_REPO="https://github.com/Phygital-Tech-Stack/claude-workflow.git"
PINNED=$(.claude/hooks/pyrun -c "import json; print(json.load(open('.claude/workflow.lock'))['version'])")
LATEST=$(git ls-remote --tags --sort=-v:refname "$MASTER_REPO" 'v*' | head -1 | sed 's/.*refs\/tags\/v//')
```

### Clone at latest version

```bash
rm -rf /tmp/claude-workflow-master
git clone --depth 1 --branch "v$LATEST" "$MASTER_REPO" /tmp/claude-workflow-master
```

### Update lock file

```bash
.claude/hooks/pyrun -c "
import json
lock_path = '.claude/workflow.lock'
with open(lock_path) as f:
    lock = json.load(f)
lock['version'] = '$LATEST'
with open(lock_path, 'w') as f:
    json.dump(lock, f, indent=2)
    f.write('\n')
"
```

## Step 3: Run Drift Check

```bash
/tmp/claude-workflow-master/tools/diff.sh --project . --master /tmp/claude-workflow-master
```

## Step 4: Sync (if --update)

```bash
/tmp/claude-workflow-master/tools/sync.sh --project . --master /tmp/claude-workflow-master
```

## Step 5: Clean Up

```bash
rm -rf /tmp/claude-workflow-master
```
