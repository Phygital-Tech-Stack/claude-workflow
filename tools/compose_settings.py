#!/usr/bin/env python3
"""Compose settings.json from base + guards + stack overlays + project overrides."""
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
                # Check command, prompt, and agent fields for GUARD: refs
                guard_ref = None
                for field in ("command", "prompt", "agent"):
                    val = hook.get(field, "")
                    if val.startswith("GUARD:"):
                        guard_ref = val.replace("GUARD:", "")
                        break
                if guard_ref and guard_ref in guards:
                    guard_def = guards[guard_ref]
                    # Copy all hook fields from guard definition
                    # Supports command, prompt, and agent hook types
                    resolved = copy.deepcopy(guard_def["hook"])
                    hook.clear()
                    hook.update(resolved)
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


def discover_agents(claude_dir: str) -> list[str]:
    """Get agent names from .claude/agents/*.md filenames."""
    agents_dir = os.path.join(claude_dir, "agents")
    if not os.path.isdir(agents_dir):
        return []
    return sorted(
        f.replace(".md", "")
        for f in os.listdir(agents_dir)
        if f.endswith(".md")
    )


def merge_overrides(settings: dict, overrides_settings: dict) -> dict:
    """Merge project overrides (from workflow.overrides.yaml) into settings.

    List-type keys under permissions and enabledMcpjsonServers are extended
    (not replaced) so project-specific entries accumulate on top of base+stack.
    """
    result = copy.deepcopy(settings)
    for key, val in overrides_settings.items():
        if key == "permissions" and isinstance(val, dict):
            if "permissions" not in result:
                result["permissions"] = {}
            for pkey, pval in val.items():
                if isinstance(pval, list):
                    existing = result["permissions"].setdefault(pkey, [])
                    existing.extend(pval)
                    result["permissions"][pkey] = list(dict.fromkeys(existing))
                else:
                    result["permissions"][pkey] = pval
        elif key == "enabledMcpjsonServers" and isinstance(val, list):
            existing = result.get("enabledMcpjsonServers", [])
            result["enabledMcpjsonServers"] = list(dict.fromkeys(existing + val))
        elif key == "hooks" and isinstance(val, dict):
            result = merge_hooks(result, {"hooks": val})
        else:
            result[key] = copy.deepcopy(val)
    return result


def dedup_hooks(settings: dict) -> dict:
    """Remove duplicate hooks within each event by command/prompt/agent hash."""
    import hashlib

    result = copy.deepcopy(settings)
    for event_key, event_groups in result.get("hooks", {}).items():
        seen: set[str] = set()
        deduped_groups = []
        for group in event_groups:
            deduped_hook_list = []
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "") or hook.get("prompt", "") or hook.get("agent", "")
                matcher = group.get("matcher", "*")
                fingerprint = f"{matcher}|{hashlib.md5(cmd.encode()).hexdigest()}"
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    deduped_hook_list.append(hook)
            if deduped_hook_list:
                deduped_group = copy.deepcopy(group)
                deduped_group["hooks"] = deduped_hook_list
                deduped_groups.append(deduped_group)
        result["hooks"][event_key] = deduped_groups
    return result


def resolve_placeholders(obj, placeholders: dict[str, str]):
    """Recursively resolve {{KEY}} placeholders in all string values."""
    if isinstance(obj, str):
        for key, val in placeholders.items():
            obj = obj.replace("{{" + key + "}}", val)
        return obj
    if isinstance(obj, dict):
        return {k: resolve_placeholders(v, placeholders) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_placeholders(item, placeholders) for item in obj]
    return obj


def main():
    parser = argparse.ArgumentParser(description="Compose settings.json from base + guards + stack overlays")
    parser.add_argument("--base", required=True, help="Path to settings.base.json")
    parser.add_argument("--guards", required=True, help="Path to guards directory")
    parser.add_argument("--stacks", required=True, help="Comma-separated stack names")
    parser.add_argument("--stacks-dir", required=True, help="Path to stacks directory")
    parser.add_argument("--output", required=True, help="Output settings.json path")
    parser.add_argument("--overrides", help="Path to workflow.overrides.yaml (optional)")
    parser.add_argument("--claude-dir", help="Path to .claude dir for agent discovery (optional)")
    parser.add_argument("--commands", help="Placeholder values as JSON string (optional)")
    parser.add_argument("--preserve-from", help="Existing settings.json to preserve permissions/enabledMcpjsonServers from")
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

    # Preserve project-specific settings from existing settings.json
    if args.preserve_from and os.path.exists(args.preserve_from):
        with open(args.preserve_from) as f:
            existing = json.load(f)
        preserved = {}
        if "permissions" in existing:
            preserved["permissions"] = existing["permissions"]
        if "enabledMcpjsonServers" in existing:
            preserved["enabledMcpjsonServers"] = existing["enabledMcpjsonServers"]
        if preserved:
            settings = merge_overrides(settings, preserved)

        # Preserve project-specific inline hooks from existing settings.
        # Skip hooks that are: managed scripts (.claude/hooks/), unresolved
        # GUARD: refs, or functionally identical to a hook already in the
        # composed settings (by command hash — catches both base guards and
        # stack guards regardless of naming).
        existing_hooks = existing.get("hooks", {})
        if existing_hooks:
            # Build a set of command hashes already in the composed settings
            import hashlib
            composed_hashes: set[str] = set()
            for event_groups in settings.get("hooks", {}).values():
                for group in event_groups:
                    for hook in group.get("hooks", []):
                        cmd = hook.get("command", "") or hook.get("prompt", "") or hook.get("agent", "")
                        if cmd:
                            composed_hashes.add(hashlib.md5(cmd.encode()).hexdigest())

            project_hooks: dict[str, list] = {}
            for event_key, event_groups in existing_hooks.items():
                project_groups = []
                for group in event_groups:
                    project_hook_list = []
                    for hook in group.get("hooks", []):
                        # Check command, prompt, and agent fields
                        cmd = hook.get("command", "") or hook.get("prompt", "") or hook.get("agent", "")
                        # Skip hooks that reference managed scripts or guards.
                        # "python3 -c" hooks are the pre-v1.6 guard format — they
                        # must be dropped so the new pyrun equivalents are not
                        # duplicated alongside them.
                        if ".claude/hooks/" in cmd or cmd.startswith("GUARD:"):
                            continue
                        if cmd.startswith("python3 -c") or cmd.startswith("python -c"):
                            continue
                        # Skip hooks that are functionally identical to a
                        # composed hook (same command text = same guard)
                        if cmd and hashlib.md5(cmd.encode()).hexdigest() in composed_hashes:
                            continue
                        project_hook_list.append(copy.deepcopy(hook))
                    if project_hook_list:
                        preserved_group = copy.deepcopy(group)
                        preserved_group["hooks"] = project_hook_list
                        project_groups.append(preserved_group)
                if project_groups:
                    project_hooks[event_key] = project_groups
            if project_hooks:
                settings = merge_hooks(settings, {"hooks": project_hooks})

    # Merge project overrides from workflow.overrides.yaml
    if args.overrides and os.path.exists(args.overrides):
        try:
            import yaml
            with open(args.overrides) as f:
                overrides = yaml.safe_load(f) or {}
            overrides_settings = overrides.get("settings", {})
            if overrides_settings:
                settings = merge_overrides(settings, overrides_settings)
        except ImportError:
            print("WARNING: PyYAML not installed — skipping workflow.overrides.yaml", file=sys.stderr)

    # Resolve placeholders
    placeholders = {}
    if args.commands:
        placeholders = json.loads(args.commands)
    if args.claude_dir:
        agents = discover_agents(args.claude_dir)
        if agents:
            placeholders["AGENT_NAMES"] = "|".join(agents)
    if placeholders:
        settings = resolve_placeholders(settings, placeholders)

    # Dedup hooks — prevents accumulation from repeated syncs with --preserve-from
    settings = dedup_hooks(settings)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
