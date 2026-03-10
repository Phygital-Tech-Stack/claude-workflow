#!/usr/bin/env python3
"""Shared utilities for claude-workflow tools.

Consolidates logic that was previously duplicated across generate_lock.py,
drift_check.py, sync.sh (3 inline copies), and init.sh.
"""
import hashlib
import json
import os


def sha256_file(path: str) -> str:
    """SHA-256 hash of a file, prefixed with 'sha256:'."""
    with open(path, "rb") as f:
        return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"


def find_master_source(master_dir: str, rel_path: str, stacks: list[str]) -> str | None:
    """Find where a managed file lives in the master repo (base or stack).

    Maps from project-relative paths (inside .claude/) back to master source
    locations. Handles the flattening that init.sh does when copying stack
    hooks and failure-patterns into .claude/hooks/.

    Examples:
        "hooks/stop-gate.sh"     → base/hooks/stop-gate.sh
        "hooks/tdd-guard.sh"     → stacks/typescript-nestjs/hooks/tdd-guard.sh
        "hooks/failure-patterns/timeout.json"
            → stacks/typescript-nestjs/failure-patterns/timeout.json
        "agents/planner.md"      → base/agents/planner.md
        "skills/commit/SKILL.md" → base/skills/commit/SKILL.md
    """
    # Check base first
    base_path = os.path.join(master_dir, "base", rel_path)
    if os.path.exists(base_path):
        return base_path

    # Check stacks — stack hooks/failure-patterns are copied flat into .claude/hooks/
    for stack in stacks:
        stack = stack.strip()
        # Direct match (e.g., commands.yaml under stack root)
        stack_path = os.path.join(master_dir, "stacks", stack, rel_path)
        if os.path.exists(stack_path):
            return stack_path

        # Hook files: project has hooks/<name>, stack has hooks/<name>
        if rel_path.startswith("hooks/"):
            hook_rel = rel_path[len("hooks/"):]
            # Check stack hooks dir
            hook_path = os.path.join(master_dir, "stacks", stack, "hooks", hook_rel)
            if os.path.exists(hook_path):
                return hook_path
            # Check failure patterns (flattened into hooks/failure-patterns/)
            if hook_rel.startswith("failure-patterns/"):
                fp_name = hook_rel[len("failure-patterns/"):]
                fp_path = os.path.join(master_dir, "stacks", stack, "failure-patterns", fp_name)
                if os.path.exists(fp_path):
                    return fp_path

        # Team files: stack teams are at stacks/{stack}/teams/<team>/...
        # which matches the direct check above (line 42-44), so no special handling needed.

    return None


def load_commands(master_dir: str, stacks: list[str], version: str) -> dict[str, str]:
    """Load placeholder values from stack commands.yaml files.

    Returns a dict of KEY → value suitable for resolving {{KEY}} placeholders.
    """
    try:
        import yaml
    except ImportError:
        return {"VERSION": version, "STACKS": ", ".join(stacks)}

    commands: dict[str, str] = {}
    for stack in stacks:
        stack = stack.strip()
        cmd_path = os.path.join(master_dir, "stacks", stack, "commands.yaml")
        if os.path.exists(cmd_path):
            with open(cmd_path) as f:
                data = yaml.safe_load(f) or {}
            for key, val in data.get("commands", {}).items():
                commands[key] = str(val)
            # Also resolve list-based values (CLASSIFY_CATEGORIES, etc.)
            for key in ("classify_categories", "critical_files", "auto_quick_patterns"):
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        commands[key.upper()] = ", ".join(str(v) for v in val)
    commands["VERSION"] = version
    commands["STACKS"] = ", ".join(stacks)
    return commands
