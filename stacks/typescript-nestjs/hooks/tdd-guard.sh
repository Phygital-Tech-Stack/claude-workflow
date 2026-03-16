#!/usr/bin/env bash
# TDD Guard — blocks new service/handler/repository files without companion test
# Stack: Phlow (TypeScript services with src/ layout)

exec py <(cat <<'PYTHON'
import json, sys, os

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

ti = data.get("tool_input", {})
path = ti.get("file_path", "")

# Only check Write operations in service source directories
if not path or "/src/" not in path:
    sys.exit(0)
if any(skip in path for skip in ["__tests__", "node_modules", ".spec.", ".test."]):
    sys.exit(0)

# Check if this is a new handler, service, or repository file
tdd_triggers = [".handler.ts", ".service.ts", ".repository.ts"]
if not any(path.endswith(t) for t in tdd_triggers):
    sys.exit(0)

# Check if companion test exists
base = path.rsplit(".", 1)[0]  # Remove .ts
test_patterns = [
    base.replace("/src/", "/__tests__/") + ".spec.ts",
    base.replace("/src/", "/__tests__/") + ".test.ts",
    base + ".spec.ts",
    base + ".test.ts",
]

for tp in test_patterns:
    if os.path.exists(tp):
        sys.exit(0)

# No test found — warn
filename = os.path.basename(path)
print(json.dumps({
    "systemMessage": f"[TDD] Writing {filename} without a companion test. Write tests first (RED phase)."
}))
sys.exit(0)
PYTHON
)
