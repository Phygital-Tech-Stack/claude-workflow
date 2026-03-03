"""Python/FastAPI failure pattern matcher for post-failure.sh dispatcher."""


def match(cmd: str, output: str) -> list[str] | None:
    """Match Python/FastAPI error patterns and return recovery suggestions."""
    suggestions = []

    # Ruff lint/format failures
    if "ruff" in cmd:
        if "syntax error" in output or "SyntaxError" in output:
            suggestions.append("Syntax error — fix the Python syntax before formatting")
        elif "import" in output and ("I001" in output or "isort" in output):
            suggestions.append("Import order — run `ruff check --fix` to auto-sort imports")
        elif "F401" in output:
            suggestions.append("Unused import — remove unused imports or use `# noqa: F401`")

    # Mypy type checking
    elif "mypy" in cmd:
        if "Cannot find implementation or library stub" in output:
            suggestions.append(
                "Missing type stubs — install stubs with "
                "`pip install types-<package>` or add to pyproject.toml"
            )
        elif "Incompatible return value" in output or "Incompatible types" in output:
            suggestions.append("Type mismatch — check function return type annotations")
        elif "has no attribute" in output:
            suggestions.append("Missing attribute — check object type and available attributes")
        else:
            suggestions.append("Type error — read the specific mypy error code and location")

    # Pytest failures
    elif "pytest" in cmd:
        if "connection refused" in output or "ConnectionError" in output:
            suggestions.append("Service not running — start required services (DB, Redis, etc.)")
        elif "timeout" in output or "TimeoutError" in output:
            suggestions.append(
                "Test timeout — check for blocking calls, "
                "missing async/await, or slow fixtures"
            )
        elif "no tests ran" in output or "collected 0 items" in output:
            suggestions.append("No tests found — check test file naming (test_*.py) and markers")
        elif "fixture" in output and "not found" in output:
            suggestions.append("Missing fixture — check conftest.py and fixture scope")
        elif "ModuleNotFoundError" in output or "ImportError" in output:
            suggestions.append("Import error — check virtual environment and `pip install -e .`")
        else:
            suggestions.append("Test failure — read assertion error for expected vs actual values")

    # Alembic migration failures
    elif "alembic" in cmd:
        if "already exists" in output:
            suggestions.append(
                "Migration conflict — a revision already targets this head. "
                "Check `alembic heads` for multiple heads."
            )
        elif "Can't locate revision" in output:
            suggestions.append(
                "Missing migration — check alembic_version table matches files in versions/"
            )
        elif "connection" in output or "OperationalError" in output:
            suggestions.append("Database connection failed — check DATABASE_URL in .env")
        else:
            suggestions.append("Alembic error — try `alembic check` to diagnose")

    # Pip/poetry/uv install failures
    elif "pip" in cmd or "poetry" in cmd or "uv" in cmd:
        if "ResolutionImpossible" in output or "version" in output:
            suggestions.append(
                "Version conflict — check dependency constraints in pyproject.toml"
            )
        elif "No matching distribution" in output:
            suggestions.append(
                "Package not found — verify package name on PyPI "
                "(AI can hallucinate package names)"
            )
        else:
            suggestions.append("Install error — try clearing cache and reinstalling")

    # Python build failures
    elif "build" in cmd or "setup.py" in cmd:
        if "ModuleNotFoundError" in output:
            suggestions.append("Missing build dependency — check [build-system] in pyproject.toml")
        elif "SyntaxError" in output:
            suggestions.append("Syntax error — fix Python syntax before building")

    return suggestions if suggestions else None
