"""PostToolUse hook: Warn about incorrect Dart import ordering."""
import json
import sys
from pathlib import Path


# Import group priority (lower = should come first)
def import_group(line: str) -> int:
    """Classify an import line into its ordering group."""
    if "import 'dart:" in line or 'import "dart:' in line:
        return 0  # SDK dart: imports
    if "import 'package:flutter/" in line or 'import "package:flutter/' in line:
        return 1  # Flutter SDK imports
    if "import 'package:phast_" in line or 'import "package:phast_' in line:
        return 3  # Shared phast_ packages
    if "import 'package:" in line or 'import "package:' in line:
        return 2  # Third-party packages
    return 4  # Relative imports


def main():
    try:
        input_data = json.load(sys.stdin)
        file_path = input_data.get("tool_input", {}).get("file_path", "")

        if not file_path:
            return 0

        path = Path(file_path)

        if path.suffix != ".dart" or not path.exists():
            return 0

        lines = path.read_text(encoding="utf-8").splitlines()

        # Collect import lines with their line numbers
        imports = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("import "):
                imports.append((i, stripped, import_group(stripped)))
            elif imports and stripped and not stripped.startswith("//"):
                # Stop at first non-import, non-comment, non-blank line
                break

        if len(imports) < 2:
            return 0

        # Check if groups are in ascending order
        prev_group = imports[0][2]
        for line_num, line_text, group in imports[1:]:
            if group < prev_group:
                print(
                    f"WARNING: Import order violation at {path.name}:{line_num} — "
                    f"expected group {_group_name(prev_group)} before "
                    f"{_group_name(group)}",
                    file=sys.stderr,
                )
                break  # One warning per file
            prev_group = group

    except Exception:
        pass

    return 0


def _group_name(group: int) -> str:
    names = {
        0: "dart:",
        1: "package:flutter/",
        2: "third-party package:",
        3: "package:phast_",
        4: "relative",
    }
    return names.get(group, "unknown")


if __name__ == "__main__":
    sys.exit(main())
