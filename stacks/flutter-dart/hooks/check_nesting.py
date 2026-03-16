"""PostToolUse hook: Warn about deep widget nesting in build() methods."""
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

        if path.suffix != ".dart" or not path.exists():
            return 0

        lines = path.read_text(encoding="utf-8").splitlines()

        in_build = False
        brace_depth = 0
        build_base_depth = 0
        max_depth = 0
        max_depth_line = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect start of build method
            if "Widget build(" in stripped and not stripped.startswith("//"):
                in_build = True
                brace_depth = 0
                build_base_depth = 0
                max_depth = 0
                max_depth_line = 0
                # Count opening brace on same line
                for ch in stripped:
                    if ch == "{":
                        if build_base_depth == 0:
                            build_base_depth = 1
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                continue

            if not in_build:
                continue

            for ch in stripped:
                if ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1

            # Track relative depth from build method body
            relative_depth = brace_depth - build_base_depth
            if relative_depth > max_depth:
                max_depth = relative_depth
                max_depth_line = i

            # End of build method
            if brace_depth <= 0:
                if max_depth > 3:
                    print(
                        f"WARNING: Widget nesting >{3} levels in build() — "
                        f"deepest at {path.name}:{max_depth_line} "
                        f"(depth {max_depth})",
                        file=sys.stderr,
                    )
                    break  # One warning per file
                in_build = False

    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
