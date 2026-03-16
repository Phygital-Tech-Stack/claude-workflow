"""PostToolUse hook: Run dart analyze on edited Dart files."""
import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
        file_path = input_data.get("tool_input", {}).get("file_path", "")

        if not file_path:
            return 0

        path = Path(file_path)

        if path.suffix != ".dart" or not path.exists():
            return 0

        # Determine which analyzer to use based on file location
        file_str = str(path)
        if "phast_backend" in file_str:
            cmd = ["dart", "analyze", "--no-fatal-infos", file_str]
        elif "phast_admin" in file_str:
            cmd = ["dart", "analyze", "--no-fatal-infos", file_str]
        else:
            cmd = ["dart", "analyze", "--no-fatal-infos", file_str]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Only report errors, not infos/warnings
        if result.returncode != 0:
            # Filter for error lines only
            for line in result.stderr.splitlines() + result.stdout.splitlines():
                if " - error - " in line.lower() or "error -" in line.lower():
                    print(f"ANALYZE: {line}", file=sys.stderr)

    except subprocess.TimeoutExpired:
        pass  # Don't block on slow analysis
    except Exception:
        pass  # Don't block the workflow

    return 0


if __name__ == "__main__":
    sys.exit(main())
