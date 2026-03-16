"""PostToolUse hook: Auto-format Dart files after Edit/Write."""
import json
import subprocess
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
            subprocess.run(
                ["dart", "format", str(path)],
                capture_output=True,
                text=True
            )
    except Exception:
        # Silently ignore errors - don't block the workflow
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
