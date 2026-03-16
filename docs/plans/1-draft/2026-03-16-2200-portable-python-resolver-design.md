# Portable Python Resolver (`pyrun`)

**Status**: Draft
**Created**: 2026-03-16
**Problem**: Phlow is developed on Windows where `python3` doesn't exist — only `py` (Windows Python launcher). All 12 base hooks, 5 stack hooks, ~7 guards, 5 settings overlays, and 1 CI template hardcode `python3`. Syncing master config to Phlow breaks every Python-backed hook.

## Decision

Ship a universal resolver script `base/hooks/pyrun` that detects the available Python interpreter (`python3` → `py` → `python`) and delegates. Replace all `python3` references across the repo to use `pyrun` instead.

## Design

### New file: `base/hooks/pyrun`

```bash
#!/usr/bin/env bash
# Universal Python resolver — finds python3, py, or python
PY=$(command -v python3 2>/dev/null \
  || command -v py 2>/dev/null \
  || command -v python 2>/dev/null)
if [ -z "$PY" ]; then
  echo '{"error":"No Python interpreter found (tried python3, py, python)"}' >&2
  exit 1
fi
exec "$PY" "$@"
```

Must be committed with executable permissions (`chmod +x`).

### Changes by category

#### 1. Base hooks (12 files)

Pattern: `exec python3 <(cat <<'PYTHON'` or `exec python3 - <<'PYTHON'`
Change to: `exec "$(dirname "$0")/pyrun" <(cat <<'PYTHON'` or `exec "$(dirname "$0")/pyrun" - <<'PYTHON'`

Files:
- `base/hooks/session-start.sh`
- `base/hooks/prompt-submit.sh`
- `base/hooks/pre-compact.sh`
- `base/hooks/context-check.sh`
- `base/hooks/subagent-start.sh`
- `base/hooks/subagent-stop.sh`
- `base/hooks/session-end.sh`
- `base/hooks/task-completed.sh`
- `base/hooks/post-failure.sh`
- `base/hooks/teammate-idle.sh`
- `base/hooks/mcp-security-scan.sh` (uses `mcp-scan` not python3 — verify, may be no-op)

#### 2. Stack hooks — bash wrappers (5 files)

**exec pattern** (same as base):
- `stacks/csharp-dotnet/hooks/tdd-guard.sh`
- `stacks/typescript-nestjs/hooks/tdd-guard.sh`

**Inline `-c` pattern**: `python3 -c "..."` → `"$(dirname "$0")/pyrun" -c "..."`
- `stacks/csharp-dotnet/hooks/dotnet_analyze.sh`
- `stacks/typescript-nestjs/hooks/prettier_format.sh`
- `stacks/typescript-nestjs/hooks/eslint_check.sh`

#### 3. Flutter .py hooks — remove shebangs (7 files)

Remove `#!/usr/bin/env python3` line (dead code once invoked via pyrun):
- `stacks/flutter-dart/hooks/check_nesting.py`
- `stacks/flutter-dart/hooks/check_print.py`
- `stacks/flutter-dart/hooks/check_deprecated.py`
- `stacks/flutter-dart/hooks/check_imports.py`
- `stacks/flutter-dart/hooks/check_file_size.py`
- `stacks/flutter-dart/hooks/dart_format.py`
- `stacks/flutter-dart/hooks/dart_analyze.py`

#### 4. Guards — JSON command strings (~7 files)

Pattern: `"command": "python3 -c \"..."` → `"command": ".claude/hooks/pyrun -c \"..."`

Files in `stacks/*/guards/`:
- `csharp-dotnet/guards/check-layer-imports.json`
- `typescript-nestjs/guards/design-doc-guard.json`
- `typescript-nestjs/guards/naming-detector.json`
- `typescript-nestjs/guards/ts-ignore-blocker.json`
- `typescript-nestjs/guards/check-layer-imports.json`
- `typescript-nestjs/guards/file-size-limits.json`
- `typescript-nestjs/guards/any-type-blocker.json`
- `flutter-dart/guards/check-layer-imports.json`
- `python-fastapi/guards/check-layer-imports.json`

#### 5. Settings overlays (1 file, 7 hook entries)

`stacks/flutter-dart/settings.overlay.json`: Change all `python3 .claude/hooks/` → `.claude/hooks/pyrun .claude/hooks/`

#### 6. CI template (1 file)

`templates/workflow-drift.yml`: Change `python3 -c` → `.claude/hooks/pyrun -c`

### What does NOT change

- `tools/validate_sync.py`, `tools/compose_settings.py`, `tools/sync_all.sh` — these are developer tools that run on the master repo machine, not synced to projects. They can keep using `python3` directly.
- `sync.sh` logic — `pyrun` is just another file in `base/hooks/`, synced like any other hook.

### Sync impact

- All managed projects get `pyrun` on next sync
- Lock checksums update for all modified files
- Projects with local edits to affected hooks will show `DIVERGED` — expected, one-time migration

## Risks

| Risk | Mitigation |
|------|------------|
| `dirname "$0"` resolves wrong when hooks are symlinked | Claude Code hooks are copied (not symlinked) to projects. Self-managed repo symlinks resolve correctly via `readlink`. |
| Windows bash doesn't support `command -v` | WSL bash supports it. Git Bash supports it. Native cmd.exe doesn't run bash hooks at all. |
| `py` launcher picks wrong Python version | `py` defaults to latest installed Python, which is fine for our stdlib-only scripts. |

## Implementation order

1. Create `base/hooks/pyrun` with executable permissions
2. Update base hooks (12 files)
3. Update stack hooks (5 files)
4. Remove flutter shebangs (7 files)
5. Update guards (9 files)
6. Update settings overlay (1 file)
7. Update CI template (1 file)
8. Run `validate_sync.py` to confirm no breakage
9. Test on Windows (Phlow) and Linux (any other project)
