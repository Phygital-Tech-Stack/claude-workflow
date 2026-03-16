"""PostToolUse hook: Warn about deprecated patterns in Dart files."""
import json
import sys
from pathlib import Path

BANNED_PATTERNS = [
    (".withOpacity(", ".withValues(alpha:)"),
    ("SysproApiClient", "UnifiedSysproClient"),
    ("EmployeeAuthService", "EmployeeAuthFacade"),
]


def main():
    try:
        input_data = json.load(sys.stdin)
        file_path = input_data.get("tool_input", {}).get("file_path", "")

        if not file_path:
            return 0

        path = Path(file_path)

        if path.suffix != ".dart" or not path.exists():
            return 0

        content = path.read_text(encoding="utf-8")

        for pattern, replacement in BANNED_PATTERNS:
            if pattern in content:
                # Find first occurrence line number
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern in line and not line.strip().startswith("//"):
                        print(
                            f"WARNING: Deprecated `{pattern}` at {path.name}:{i} "
                            f"— use `{replacement}` instead",
                            file=sys.stderr,
                        )
                        break  # One warning per pattern per file

    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
