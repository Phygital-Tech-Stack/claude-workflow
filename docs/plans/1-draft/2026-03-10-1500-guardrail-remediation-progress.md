# Progress: Guardrail Gap Remediation (D3, D7, D19)

**Design**: docs/plans/1-draft/2026-03-10-1500-guardrail-remediation-design.md
**Status**: IN PROGRESS
**Last session**: 2026-03-10

## Completed

1. Blueprint update — added Layer Boundaries section to coding-conventions.template.md
2. Per-stack `check-layer-imports.json` guards for all 4 stacks
3. typescript-nestjs PostToolUse hooks (prettier_format.sh, eslint_check.sh)
4. csharp-dotnet PostToolUse hook (dotnet_analyze.sh)
5. Base `check-file-size.json` guard
6. `decisions.log.template` in base/templates/
7. `co-authored-by.json` guard in base/guards/
8. `owasp-asi-mapping.md` in docs/
9. All settings overlay files updated (4 stacks + base)

## Current

Pending: lock file regeneration and validation

## Blocked

(nothing)

## Next Session Should

1. Run /validate-change
2. Regenerate lock file
3. /commit
