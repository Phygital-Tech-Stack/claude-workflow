# claude-workflow

Canonical master repository for AI development workflows across the Phygital Tech Stack. Keeps Claude Code configuration — hooks, guards, skills, agents, blueprints — in sync across all projects.

## Architecture

```
claude-workflow/
├── base/                    # Generic workflow (all projects)
│   ├── WORKFLOW.md          # Master workflow document
│   ├── hooks/               # Lifecycle hooks (session-start, pre-compact, etc.)
│   ├── guards/              # Guard definitions (env-secrets, quick-fix-blocker, etc.)
│   ├── skills/              # Core skills (commit, tdd, validate-change, etc.)
│   ├── agents/              # Agent templates (code-reviewer)
│   └── blueprints/          # Blueprint templates (coding-conventions, testing-patterns)
├── stacks/                  # Technology-specific overlays
│   ├── typescript-nestjs/   # ERP, PhLOW (TypeScript stack)
│   ├── flutter-dart/        # PhAST (Flutter/Dart stack)
│   ├── python-fastapi/      # PhAZE (Python/FastAPI stack)
│   └── csharp-dotnet/       # PhLOW (C#/.NET stack)
├── tools/                   # Sync engine
│   ├── init.sh              # Initialize a project
│   ├── compose_settings.py  # Merge base + guards + overlays → settings.json
│   ├── diff.sh              # Drift detection (three-way checksum)
│   ├── drift_check.py       # Drift detection engine
│   ├── sync.sh              # Pull updates from master
│   └── promote.sh           # Promote project file → master
├── templates/               # CI templates for project repos
├── tests/                   # Integration tests
├── version.json             # Current version (semver)
└── projects.json            # Registry of managed projects
```

## Quick Start

### Initialize a new project

```bash
./tools/init.sh --project /path/to/project --stacks typescript-nestjs
```

This copies base + stack files into the project's `.claude/` directory, composes `settings.json`, and generates `workflow.lock` + `workflow.overrides.yaml`.

### Check for drift

```bash
./tools/diff.sh --project /path/to/project
```

Reports per-file status: `CURRENT`, `BEHIND`, `DIVERGED`, `LOCAL-EDIT`, or `MISSING`.

### Sync updates

```bash
./tools/sync.sh --project /path/to/project [--auto]
```

Auto-updates `BEHIND` files, warns on `DIVERGED` and `LOCAL-EDIT`. Use `--auto` for non-interactive mode.

### Promote a project file to master

```bash
./tools/promote.sh --file hooks/my-new-hook.sh --from /path/to/project --target base
```

### From within a project (via skill)

```
/sync-workflow --check    # Check drift status
/sync-workflow --update   # Pull updates
```

## How It Works

### Settings Composition

`compose_settings.py` merges three layers:

1. **Base settings** (`base/settings.base.json`) — lifecycle hooks, `GUARD:` references
2. **Guard definitions** (`base/guards/*.json`) — resolves `GUARD:` to inline Python
3. **Stack overlays** (`stacks/<stack>/settings.overlay.json`) — stack-specific hooks

### Three-Way Drift Detection

Compares checksums from three sources:

| Local vs Lock | Lock vs Master | Status |
|--------------|----------------|--------|
| match | match | `CURRENT` |
| match | differ | `BEHIND` |
| differ | differ | `DIVERGED` |
| differ | match | `LOCAL-EDIT` |
| missing | — | `MISSING` |

### Workflow Lock

`.claude/workflow.lock` tracks the pinned version and SHA-256 checksums of all managed files. Updated by `init.sh` and `sync.sh`.

### Overrides

`.claude/workflow.overrides.yaml` lets projects:
- Exclude files from sync (project-owned customizations)
- Specify additional settings merged on top
- Override blueprint sections

## Stack Overlays

Each stack provides:
- `commands.yaml` — maps `{{PLACEHOLDER}}` names to actual commands
- `settings.overlay.json` — stack-specific hooks (linters, formatters)
- `hooks/` — stack-specific hook scripts
- `failure-patterns/<lang>.py` — error pattern matching for `post-failure.sh`
- `guards/` — stack-specific guard definitions (optional)

## Versioning

Follows [semver](https://semver.org/):
- **Major**: Breaking changes to workflow structure or tool CLI
- **Minor**: New skills, hooks, guards, or stack overlays
- **Patch**: Bug fixes, wording improvements

Version is in `version.json`. Pushing a version change to `main` auto-creates a GitHub release via CI.

## Projects

| Project | Stack(s) | Repo |
|---------|----------|------|
| ERP | typescript-nestjs | Phygital-Tech-Stack/erp |
| PhAST | flutter-dart | Phygital-Tech-Stack/phast |
| PhAZE | python-fastapi | Phygital-Tech-Stack/phaze |
| PhLOW | typescript-nestjs, csharp-dotnet | Phygital-Tech-Stack/phlow |
