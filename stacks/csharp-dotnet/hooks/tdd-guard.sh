#!/usr/bin/env bash
# TDD Guard — blocks new service/controller/repository files without companion test
# Stack: csharp-dotnet

exec python3 <(cat <<'PYTHON'
import json, sys, os

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

ti = data.get("tool_input", {})
path = ti.get("file_path", "")

# Only check Write operations on C# files
if not path or not path.endswith(".cs"):
    sys.exit(0)
if any(skip in path for skip in ["Tests/", ".Tests/", "Tests.cs"]):
    sys.exit(0)

# Check if this is a new service, controller, or repository file
tdd_triggers = ["Service.cs", "Controller.cs", "Repository.cs"]
if not any(path.endswith(t) for t in tdd_triggers):
    sys.exit(0)

# Check if companion test exists
# Convention: src/Project/Services/FooService.cs → tests/Project.Tests/Services/FooServiceTests.cs
basename = os.path.basename(path)
name_no_ext = basename[:-3]  # Remove .cs
test_name = name_no_ext + "Tests.cs"

dir_of_file = os.path.dirname(path)
test_patterns = []

# Pattern 1: Parallel test project (src/Proj/X.cs → tests/Proj.Tests/XTests.cs)
if "/src/" in path:
    test_path = path.replace("/src/", "/tests/")
    test_dir = os.path.dirname(test_path)
    parts = test_dir.split("/")
    for i, part in enumerate(parts):
        if i > 0 and parts[i - 1] == "tests":
            parts[i] = part + ".Tests"
            break
    test_patterns.append(os.path.join("/".join(parts), test_name))

# Pattern 2: Same directory with Tests suffix
test_patterns.append(os.path.join(dir_of_file, test_name))

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
