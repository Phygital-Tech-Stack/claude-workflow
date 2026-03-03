#!/usr/bin/env python3
"""Compose settings.json from base + guards + stack overlays."""
import argparse
import copy
import json
import os
import sys


def load_guards(guards_dir: str) -> dict[str, dict]:
    """Load guard definitions from JSON files."""
    guards = {}
    if not os.path.isdir(guards_dir):
        return guards
    for f in os.listdir(guards_dir):
        if not f.endswith(".json"):
            continue
        name = f.replace(".json", "")
        with open(os.path.join(guards_dir, f)) as fh:
            guards[name] = json.load(fh)
    return guards


def resolve_guard_refs(settings: dict, guards: dict) -> dict:
    """Replace GUARD:name references with actual hook commands."""
    result = copy.deepcopy(settings)
    for event_key, event_hooks in result.get("hooks", {}).items():
        for hook_group in event_hooks:
            for hook in hook_group.get("hooks", []):
                cmd = hook.get("command", "")
                if cmd.startswith("GUARD:"):
                    guard_name = cmd.replace("GUARD:", "")
                    if guard_name in guards:
                        guard_def = guards[guard_name]
                        hook["command"] = guard_def["hook"]["command"]
                        if "timeout" in guard_def["hook"]:
                            hook["timeout"] = guard_def["hook"]["timeout"]
    return result


def merge_hooks(base: dict, overlay: dict) -> dict:
    """Deep merge overlay hooks into base."""
    result = copy.deepcopy(base)
    for event_key, event_hooks in overlay.get("hooks", {}).items():
        if event_key not in result.get("hooks", {}):
            if "hooks" not in result:
                result["hooks"] = {}
            result["hooks"][event_key] = []
        result["hooks"][event_key].extend(copy.deepcopy(event_hooks))
    # Merge top-level keys other than hooks
    for key in overlay:
        if key != "hooks":
            if key in result and isinstance(result[key], dict) and isinstance(overlay[key], dict):
                result[key].update(overlay[key])
            else:
                result[key] = copy.deepcopy(overlay[key])
    return result


def main():
    parser = argparse.ArgumentParser(description="Compose settings.json from base + guards + stack overlays")
    parser.add_argument("--base", required=True, help="Path to settings.base.json")
    parser.add_argument("--guards", required=True, help="Path to guards directory")
    parser.add_argument("--stacks", required=True, help="Comma-separated stack names")
    parser.add_argument("--stacks-dir", required=True, help="Path to stacks directory")
    parser.add_argument("--output", required=True, help="Output settings.json path")
    args = parser.parse_args()

    # Load base
    with open(args.base) as f:
        settings = json.load(f)

    # Load and resolve guards
    guards = load_guards(args.guards)
    settings = resolve_guard_refs(settings, guards)

    # Apply stack overlays
    for stack in args.stacks.split(","):
        stack = stack.strip()
        if not stack:
            continue
        overlay_path = os.path.join(args.stacks_dir, stack, "settings.overlay.json")
        if os.path.exists(overlay_path):
            with open(overlay_path) as f:
                overlay = json.load(f)
            # Load stack-specific guards
            stack_guards_dir = os.path.join(args.stacks_dir, stack, "guards")
            if os.path.isdir(stack_guards_dir):
                stack_guards = load_guards(stack_guards_dir)
                overlay = resolve_guard_refs(overlay, stack_guards)
            settings = merge_hooks(settings, overlay)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
