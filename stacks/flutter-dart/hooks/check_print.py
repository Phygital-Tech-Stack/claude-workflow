"""PostToolUse hook: Warn about print() statements in Dart files."""
import json
import re
import sys
from pathlib import Path


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract file path
        file_path = input_data.get("tool_input", {}).get("file_path", "")

        if not file_path:
            return 0

        path = Path(file_path)

        # Check if it's a Dart file and exists
        if path.suffix == ".dart" and path.exists():
            content = path.read_text(encoding="utf-8")

            # Check for print( statements (excluding comments)
            # Simple check - look for print( not preceded by //
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Skip comment lines
                stripped = line.strip()
                if stripped.startswith("//"):
                    continue

                # Check for print(
                if re.search(r'\bprint\s*\(', line):
                    print(
                        f"WARNING: print() found in {path}:{i} - "
                        "consider removing before commit",
                        file=sys.stderr
                    )
                    break  # Only warn once per file

    except Exception:
        # Silently ignore errors - don't block the workflow
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
