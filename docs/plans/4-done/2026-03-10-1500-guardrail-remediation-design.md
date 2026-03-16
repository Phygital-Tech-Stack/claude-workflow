# Design: Guardrail Gap Remediation (D3, D7, D19)

**Date**: 2026-03-10 15:00
**Status**: Approved
**Author**: User + Claude

## Problem Statement

Score-guardrails assessment (192/250) identified three gaps limiting the workflow's maturity:
- **D3 Architecture Boundaries** (3/5): No automated cross-layer import enforcement
- **D7 PostToolUse Hooks** (3/5): typescript-nestjs has zero PostToolUse hooks; no base file-size check
- **D19 Regulatory Compliance** (3/5): No decisions.log format, no Co-Authored-By enforcement, no structured OWASP ASI mapping

Target: D3→4, D7→4, D19→4. Projected score: ~205/250.

## Decision

Per-stack pattern: each stack gets its own enforcement hooks (following existing convention). Compliance artifacts go in base/. Advisory severity for new hooks (not blockers) except file-size hard limit.

## Design

### D3: Architecture Boundary Hooks

**Per-stack `check_layer_imports.py`** — PreToolUse guard on `Edit|Write`.

Each hook extracts import statements using stack-appropriate regex and checks against hardcoded layer rules:

| Stack | Layers (top→bottom) | Forbidden |
|-------|---------------------|-----------|
| typescript-nestjs | controller → service → repository → entity | Controller ✗ Repository/Entity; Service ✗ Controller |
| flutter-dart | screen → widget → provider → repository → model | Screen ✗ Repository/Model |
| python-fastapi | router → service → repository → model | Router ✗ Repository/Model |
| csharp-dotnet | controller → service → repository → entity | Controller ✗ Repository/Entity; Service ✗ Controller |

**Severity**: Advisory (`systemMessage`). Warns but does not block — legitimate exceptions exist.

**Blueprint update**: Add "Layer Boundaries" section to `base/blueprints/coding-conventions.template.md`.

### D7: PostToolUse Hooks

**typescript-nestjs** (new):
- `prettier_format.sh` — auto-format on `Edit|Write` for `.ts`, `.tsx` files
- `eslint_check.sh` — lint check on `Edit|Write`, advisory warnings

**csharp-dotnet** (new):
- `dotnet_analyze.sh` — Roslyn analyzer on `Edit|Write`, advisory warnings

**Base** (new):
- `check_file_size.py` — PostToolUse on `Edit|Write` for all stacks
  - Soft limit: 300 lines (screens/controllers), 500 lines (services) → advisory
  - Hard limit: 600 lines → blocker
  - Skip: `.md`, `.json`, `.yaml`, `.lock`, test files
  - Override via env: `WORKFLOW_FILE_SIZE_SOFT`, `WORKFLOW_FILE_SIZE_HARD`
  - flutter-dart's existing `check_file_size.py` takes precedence via stack overlay

### D19: Regulatory Compliance Artifacts

**1. decisions.log format** — `base/templates/decisions.log.template`:
```
## YYYY-MM-DD HH:mm — [DECISION TITLE]
**Context**: [Why this decision was needed]
**Decision**: [What was decided]
**Alternatives**: [What was considered and rejected]
**Consequences**: [What this means going forward]
```
SessionStart hook creates the file from template if absent.

**2. Co-Authored-By enforcement** — `base/guards/co-authored-by.py`:
PostToolUse hook on `Bash`. Checks if command was `git commit`, reads last commit message, warns if `Co-Authored-By` trailer missing. Advisory severity.

**3. OWASP ASI mapping** — `docs/owasp-asi-mapping.md`:
Structured table mapping all 10 OWASP ASI risks to specific workflow mitigations with evidence file paths.

## File Structure & Sizing

| File | Purpose | Est. Lines | New/Modified |
|------|---------|-----------|--------------|
| `stacks/typescript-nestjs/guards/check_layer_imports.py` | Layer boundary enforcement | 60 | New |
| `stacks/flutter-dart/guards/check_layer_imports.py` | Layer boundary enforcement | 60 | New |
| `stacks/python-fastapi/guards/check_layer_imports.py` | Layer boundary enforcement | 60 | New |
| `stacks/csharp-dotnet/guards/check_layer_imports.py` | Layer boundary enforcement | 60 | New |
| `stacks/typescript-nestjs/hooks/prettier_format.sh` | Auto-format PostToolUse | 25 | New |
| `stacks/typescript-nestjs/hooks/eslint_check.sh` | Lint check PostToolUse | 30 | New |
| `stacks/csharp-dotnet/hooks/dotnet_analyze.sh` | Roslyn analyzer PostToolUse | 30 | New |
| `base/guards/check_file_size.py` | Universal file-size check | 50 | New |
| `base/templates/decisions.log.template` | decisions.log format spec | 15 | New |
| `base/guards/co-authored-by.py` | Co-Authored-By enforcement | 35 | New |
| `docs/owasp-asi-mapping.md` | OWASP ASI risk mapping | 80 | New |
| `base/blueprints/coding-conventions.template.md` | Add layer boundary rules | +30 | Modified |
| `stacks/typescript-nestjs/settings.overlay.json` | Add PreToolUse + PostToolUse | +20 | Modified |
| `stacks/flutter-dart/settings.overlay.json` | Add PreToolUse entry | +8 | Modified |
| `stacks/python-fastapi/settings.overlay.json` | Add PreToolUse entry | +8 | Modified |
| `stacks/csharp-dotnet/settings.overlay.json` | Add PreToolUse + PostToolUse | +15 | Modified |
| `base/settings.base.json` | Add file-size + co-authored-by | +15 | Modified |

### Reuse Assessment

- [x] Checked existing hooks for overlapping logic (flutter-dart file-size hook exists, won't conflict)
- [x] Checked existing guards for similar patterns (import ordering exists, boundaries are new)
- [x] Identified components that should be shared from day one (file-size check in base)
- [x] Verified no file will exceed its soft size limit

## Alternatives Considered

**Base-first pattern**: Generic import-boundary hook in base with per-stack YAML config. Rejected because it adds a config file format and parsing complexity. Per-stack scripts are simpler, self-contained, and follow the existing stack overlay convention.

## Testing Plan

- Existing test infrastructure (`tests/`) covers init, sync, drift — new hooks need manual testing via `echo '{}' | python3 hook.py`
- Each hook should handle missing files, non-code files, and empty content gracefully
- Layer import hooks should pass when imports are within the same layer

## Implementation Order

1. D3: Blueprint update (coding-conventions.template.md) — establishes the rules
2. D3: Per-stack `check_layer_imports.py` + settings.overlay.json updates
3. D7: typescript-nestjs PostToolUse hooks + settings.overlay.json
4. D7: csharp-dotnet `dotnet_analyze.sh` + settings.overlay.json
5. D7: Base `check_file_size.py` + settings.base.json
6. D19: `decisions.log.template` + SessionStart hook update
7. D19: `co-authored-by.py` + settings.base.json
8. D19: `owasp-asi-mapping.md`
9. Lock file regeneration (`python3 tools/generate_lock.py`)

## Risks

- **False positives**: Layer boundary hooks may warn on legitimate cross-layer imports (e.g., shared types). Mitigated by advisory severity.
- **Tool availability**: PostToolUse format/lint hooks assume tools are installed (`prettier`, `eslint`, `dotnet`). Hooks should exit silently if tool not found.
- **Lock file drift**: Adding ~15 new files requires lock regeneration. Risk of forgetting → `/sync-workflow --check` would flag it.
