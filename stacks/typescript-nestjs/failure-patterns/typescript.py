"""TypeScript/NestJS failure pattern matcher for post-failure.sh dispatcher."""


def match(cmd: str, output: str) -> list[str] | None:
    """Match TypeScript/NestJS error patterns and return recovery suggestions."""
    suggestions = []

    # Nx lint failures
    if "nx" in cmd and "lint" in cmd:
        if "enforce-module-boundaries" in output:
            suggestions.append(
                "Nx boundary violation — modules can only import via "
                "exported services, not repositories"
            )
        elif "eslint" in output and "error" in output:
            suggestions.append(
                "ESLint errors — run `pnpm nx affected -t lint --fix` "
                "for auto-fixable issues"
            )

    # TypeScript type errors
    if "typecheck" in cmd or "tsc" in cmd:
        if "cannot find module" in output:
            if "shared-types" in output or "@erp/" in output:
                suggestions.append(
                    "Missing shared types module — run "
                    "`pnpm nx build shared-types` first"
                )
            else:
                suggestions.append(
                    "Module not found — check imports and run `pnpm install`"
                )
        elif "not assignable" in output:
            suggestions.append(
                "Type mismatch — check the type definitions in libs/shared-types/"
            )
        elif "has no exported member" in output:
            suggestions.append(
                "Missing export — add the member to the module's index.ts"
            )

    # Nx build failures
    if "nx" in cmd and "build" in cmd:
        if "out of memory" in output or "heap" in output:
            suggestions.append(
                "Out of memory — try NODE_OPTIONS='--max-old-space-size=4096'"
            )
        elif "circular" in output:
            suggestions.append(
                "Circular dependency — run `pnpm nx graph` to visualize"
            )

    # Nx test failures
    if "nx" in cmd and "test" in cmd:
        if "cannot find module" in output:
            suggestions.append(
                "Test module resolution failed — check tsconfig.spec.json paths"
            )
        elif "timeout" in output:
            suggestions.append(
                "Test timeout — increase timeout or check for unresolved promises"
            )

    # Drizzle/migration failures
    if "drizzle" in cmd:
        if "already exists" in output:
            suggestions.append(
                "Migration conflict — a migration with this name already exists. "
                "Use a different name or resolve the conflict."
            )
        elif "connection" in output or "database" in output:
            suggestions.append(
                "Database connection failed — check DATABASE_URL in .env"
            )
        else:
            suggestions.append(
                "Drizzle error — try `npx drizzle-kit check` to diagnose"
            )

    # pnpm failures
    if "pnpm" in cmd and "install" in cmd:
        if "lockfile" in output:
            suggestions.append(
                "Lockfile conflict — run `pnpm install --no-frozen-lockfile`"
            )

    return suggestions if suggestions else None
