#!/usr/bin/env python3
"""Tests for compose_settings.py."""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "tools")
COMPOSE = os.path.join(TOOLS_DIR, "compose_settings.py")


def run_compose(base_path, guards_dir, stacks, stacks_dir, output_path):
    """Run compose_settings.py and return the result."""
    result = subprocess.run(
        [
            sys.executable, COMPOSE,
            "--base", base_path,
            "--guards", guards_dir,
            "--stacks", stacks,
            "--stacks-dir", stacks_dir,
            "--output", output_path,
        ],
        capture_output=True,
        text=True,
    )
    return result


def test_guard_resolution():
    """GUARD: references should be replaced with actual commands from guard JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        # Base settings with GUARD: reference
        base = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [{"type": "command", "command": "GUARD:my-guard"}],
                    }
                ]
            }
        }
        base_path = os.path.join(tmp, "base.json")
        with open(base_path, "w") as f:
            json.dump(base, f)

        # Guard definition
        guards_dir = os.path.join(tmp, "guards")
        os.makedirs(guards_dir)
        guard = {
            "event": "PreToolUse",
            "matcher": "Edit|Write",
            "hook": {
                "type": "command",
                "command": "python3 -c 'print(\"guard ran\")'",
                "timeout": 5000,
            },
        }
        with open(os.path.join(guards_dir, "my-guard.json"), "w") as f:
            json.dump(guard, f)

        # Empty stacks dir
        stacks_dir = os.path.join(tmp, "stacks")
        os.makedirs(stacks_dir)

        output = os.path.join(tmp, "output.json")
        result = run_compose(base_path, guards_dir, "", stacks_dir, output)
        assert result.returncode == 0, f"compose failed: {result.stderr}"

        with open(output) as f:
            settings = json.load(f)

        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        assert hook["command"] == "python3 -c 'print(\"guard ran\")'", (
            f"Guard not resolved: {hook['command']}"
        )
        assert hook["timeout"] == 5000, f"Timeout not copied: {hook}"


def test_stack_overlay_merge():
    """Stack overlay hooks should be appended to base hooks."""
    with tempfile.TemporaryDirectory() as tmp:
        # Base settings
        base = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Edit",
                        "hooks": [{"type": "command", "command": "base-hook"}],
                    }
                ]
            }
        }
        base_path = os.path.join(tmp, "base.json")
        with open(base_path, "w") as f:
            json.dump(base, f)

        guards_dir = os.path.join(tmp, "guards")
        os.makedirs(guards_dir)

        # Stack overlay
        stacks_dir = os.path.join(tmp, "stacks")
        stack_dir = os.path.join(stacks_dir, "my-stack")
        os.makedirs(stack_dir)
        overlay = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Write",
                        "hooks": [{"type": "command", "command": "stack-hook"}],
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "Edit",
                        "hooks": [{"type": "command", "command": "stack-post"}],
                    }
                ],
            }
        }
        with open(os.path.join(stack_dir, "settings.overlay.json"), "w") as f:
            json.dump(overlay, f)

        output = os.path.join(tmp, "output.json")
        result = run_compose(base_path, guards_dir, "my-stack", stacks_dir, output)
        assert result.returncode == 0, f"compose failed: {result.stderr}"

        with open(output) as f:
            settings = json.load(f)

        # Base PreToolUse + stack PreToolUse
        assert len(settings["hooks"]["PreToolUse"]) == 2, (
            f"Expected 2 PreToolUse groups, got {len(settings['hooks']['PreToolUse'])}"
        )
        # Stack added PostToolUse
        assert "PostToolUse" in settings["hooks"], "PostToolUse not added from overlay"
        assert len(settings["hooks"]["PostToolUse"]) == 1


def test_stack_guard_resolution():
    """Stack-specific GUARD: references should resolve from stack guards dir."""
    with tempfile.TemporaryDirectory() as tmp:
        base = {"hooks": {}}
        base_path = os.path.join(tmp, "base.json")
        with open(base_path, "w") as f:
            json.dump(base, f)

        guards_dir = os.path.join(tmp, "guards")
        os.makedirs(guards_dir)

        # Stack with GUARD: ref and its own guard
        stacks_dir = os.path.join(tmp, "stacks")
        stack_dir = os.path.join(stacks_dir, "ts")
        stack_guards = os.path.join(stack_dir, "guards")
        os.makedirs(stack_guards)

        overlay = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Write",
                        "hooks": [{"type": "command", "command": "GUARD:ts-guard"}],
                    }
                ]
            }
        }
        with open(os.path.join(stack_dir, "settings.overlay.json"), "w") as f:
            json.dump(overlay, f)

        guard = {
            "event": "PreToolUse",
            "hook": {"type": "command", "command": "echo ts-specific"},
        }
        with open(os.path.join(stack_guards, "ts-guard.json"), "w") as f:
            json.dump(guard, f)

        output = os.path.join(tmp, "output.json")
        result = run_compose(base_path, guards_dir, "ts", stacks_dir, output)
        assert result.returncode == 0, f"compose failed: {result.stderr}"

        with open(output) as f:
            settings = json.load(f)

        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        assert hook["command"] == "echo ts-specific", (
            f"Stack guard not resolved: {hook['command']}"
        )


def test_multiple_stacks():
    """Multiple stacks should all be merged."""
    with tempfile.TemporaryDirectory() as tmp:
        base = {"hooks": {"PostToolUse": []}}
        base_path = os.path.join(tmp, "base.json")
        with open(base_path, "w") as f:
            json.dump(base, f)

        guards_dir = os.path.join(tmp, "guards")
        os.makedirs(guards_dir)

        stacks_dir = os.path.join(tmp, "stacks")
        for name, cmd in [("stack-a", "hook-a"), ("stack-b", "hook-b")]:
            d = os.path.join(stacks_dir, name)
            os.makedirs(d)
            overlay = {
                "hooks": {
                    "PostToolUse": [
                        {"matcher": "Edit", "hooks": [{"type": "command", "command": cmd}]}
                    ]
                }
            }
            with open(os.path.join(d, "settings.overlay.json"), "w") as f:
                json.dump(overlay, f)

        output = os.path.join(tmp, "output.json")
        result = run_compose(base_path, guards_dir, "stack-a,stack-b", stacks_dir, output)
        assert result.returncode == 0, f"compose failed: {result.stderr}"

        with open(output) as f:
            settings = json.load(f)

        assert len(settings["hooks"]["PostToolUse"]) == 2


if __name__ == "__main__":
    tests = [
        test_guard_resolution,
        test_stack_overlay_merge,
        test_stack_guard_resolution,
        test_multiple_stacks,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
