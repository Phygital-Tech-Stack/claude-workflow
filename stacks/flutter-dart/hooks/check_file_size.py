"""PostToolUse hook: Block screen files exceeding 1000 lines, warn above 600."""
import json
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
        file_path = input_data.get("tool_input", {}).get("file_path", "")

        if not file_path:
            return 0

        path = Path(file_path)

        # Only check *_screen.dart files
        if path.suffix != ".dart" or not path.name.endswith("_screen.dart"):
            return 0

        if not path.exists():
            return 0

        line_count = len(path.read_text(encoding="utf-8").splitlines())

        if line_count > 1000:
            print(
                f"BLOCKED: {path.name} is {line_count} lines — exceeds 1000-line "
                "hard limit. Extract components before continuing.",
                file=sys.stderr,
            )
            return 2

        if line_count > 600:
            print(
                f"WARNING: {path.name} is {line_count} lines — exceeds 600-line "
                "soft limit. Consider extraction.",
                file=sys.stderr,
            )

    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
