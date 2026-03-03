#!/usr/bin/env python3
"""Three-way checksum drift detection between project and master."""
import argparse
import hashlib
import json
import os
import sys


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"


def sha256_resolved(path: str, commands: dict[str, str]) -> str:
    """Hash a file after resolving {{PLACEHOLDER}} values."""
    with open(path, "r") as f:
        content = f.read()
    for key, val in commands.items():
        content = content.replace("{{" + key + "}}", val)
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


def load_commands(master_dir: str, stacks: list[str], version: str) -> dict[str, str]:
    """Load placeholder values from stack commands.yaml files."""
    try:
        import yaml
    except ImportError:
        return {}

    commands: dict[str, str] = {}
    for stack in stacks:
        cmd_path = os.path.join(master_dir, "stacks", stack.strip(), "commands.yaml")
        if os.path.exists(cmd_path):
            with open(cmd_path) as f:
                data = yaml.safe_load(f) or {}
            for key, val in data.get("commands", {}).items():
                commands[key] = str(val)
            for key in ("classify_categories", "critical_files", "auto_quick_patterns"):
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        commands[key.upper()] = ", ".join(str(v) for v in val)
    commands["VERSION"] = version
    commands["STACKS"] = ", ".join(stacks)
    return commands


def find_master_source(master_dir: str, rel_path: str, stacks: list[str]) -> str | None:
    """Find where a file lives in the master repo (base or stack).

    Maps from project-relative paths back to master source locations.
    E.g., "hooks/tdd-guard.sh" might be in stacks/typescript-nestjs/hooks/tdd-guard.sh
    """
    # Check base first
    base_path = os.path.join(master_dir, "base", rel_path)
    if os.path.exists(base_path):
        return base_path

    # Check stacks — stack hooks/failure-patterns are copied flat into .claude/hooks/
    for stack in stacks:
        # Direct match (e.g., commands.yaml under stack root)
        stack_path = os.path.join(master_dir, "stacks", stack, rel_path)
        if os.path.exists(stack_path):
            return stack_path

        # Hook files: project has hooks/<name>, stack has hooks/<name>
        if rel_path.startswith("hooks/"):
            hook_rel = rel_path[len("hooks/"):]
            # Check stack hooks
            hook_path = os.path.join(master_dir, "stacks", stack, "hooks", hook_rel)
            if os.path.exists(hook_path):
                return hook_path
            # Check failure patterns (flattened into hooks/failure-patterns/)
            fp_path = os.path.join(master_dir, "stacks", stack, "failure-patterns", hook_rel.replace("failure-patterns/", ""))
            if os.path.exists(fp_path):
                return fp_path

    return None


def main():
    parser = argparse.ArgumentParser(description="Three-way checksum drift detection")
    parser.add_argument("--project", required=True, help="Path to project root")
    parser.add_argument("--master", required=True, help="Path to master workflow repo")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    args = parser.parse_args()

    claude_dir = os.path.join(args.project, ".claude")
    lock_path = os.path.join(claude_dir, "workflow.lock")

    if not os.path.exists(lock_path):
        print("ERROR: No workflow.lock found. Run tools/init.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(lock_path) as f:
        lock = json.load(f)

    # Load excludes from overrides
    overrides_path = os.path.join(claude_dir, "workflow.overrides.yaml")
    excludes: set[str] = set()
    if os.path.exists(overrides_path):
        try:
            import yaml
            with open(overrides_path) as f:
                overrides = yaml.safe_load(f) or {}
            excludes = set(overrides.get("exclude", []) or [])
        except ImportError:
            # PyYAML not available, skip excludes
            pass

    stacks = lock.get("stacks", [])
    version = lock.get("version", "0.0.0")
    commands = load_commands(args.master, stacks, version)
    results = []

    master_checksums = lock.get("masterChecksums", {})

    for rel_path, lock_hash in lock.get("managed", {}).items():
        # Skip excluded files
        if any(rel_path.startswith(ex.rstrip("/")) for ex in excludes):
            continue

        # Skip the lock file itself
        if rel_path == "workflow.lock":
            continue

        local_path = os.path.join(claude_dir, rel_path)
        master_path = find_master_source(args.master, rel_path, stacks)

        local_exists = os.path.exists(local_path)
        master_exists = master_path is not None and os.path.exists(master_path)

        if not local_exists:
            results.append({"file": rel_path, "status": "MISSING"})
            continue

        local_hash = sha256(local_path)

        # Detect master changes using masterChecksums from the lock.
        # This avoids false drift when local formatters (e.g., prettier)
        # modify files after init/sync — we compare master-to-master
        # (raw source hash at sync time vs raw source hash now).
        if rel_path in master_checksums and master_exists:
            # Compare raw master source hash at sync time vs current.
            # masterChecksums stores raw (pre-resolution) hashes, so we
            # compare raw-to-raw to avoid false drift from local formatters.
            current_master_hash = sha256(master_path)
            master_changed = master_checksums[rel_path] != current_master_hash
        elif master_exists:
            # Fallback for locks without masterChecksums (pre-upgrade)
            if master_path.endswith(".md") and commands:
                master_hash = sha256_resolved(master_path, commands)
            else:
                master_hash = sha256(master_path)
            master_changed = lock_hash != master_hash
        else:
            master_changed = False

        local_matches_lock = local_hash == lock_hash
        lock_matches_master = not master_changed

        if local_matches_lock and lock_matches_master:
            status = "CURRENT"
        elif local_matches_lock and not lock_matches_master:
            status = "BEHIND"
        elif not local_matches_lock and not lock_matches_master:
            status = "DIVERGED"
        else:  # local != lock, lock == master
            status = "LOCAL-EDIT"

        entry = {"file": rel_path, "status": status}
        if status == "LOCAL-EDIT" and master_path:
            entry["master_source"] = os.path.relpath(master_path, args.master)
        results.append(entry)

    # Output
    if args.format == "json":
        print(json.dumps({"version": lock.get("version"), "results": results}, indent=2))
    else:
        behind = [r for r in results if r["status"] == "BEHIND"]
        diverged = [r for r in results if r["status"] == "DIVERGED"]
        local_edit = [r for r in results if r["status"] == "LOCAL-EDIT"]
        current = [r for r in results if r["status"] == "CURRENT"]
        missing = [r for r in results if r["status"] == "MISSING"]

        print(f"Workflow Drift Report (pinned: v{lock.get('version')})")
        print(f"  CURRENT:    {len(current)} files")
        print(f"  BEHIND:     {len(behind)} files")
        print(f"  DIVERGED:   {len(diverged)} files")
        print(f"  LOCAL-EDIT: {len(local_edit)} files")
        print(f"  MISSING:    {len(missing)} files")

        if behind:
            print("\nBEHIND (auto-update available):")
            for r in behind:
                print(f"  - {r['file']}")
        if diverged:
            print("\nDIVERGED (manual merge needed):")
            for r in diverged:
                print(f"  - {r['file']}")
        if local_edit:
            print("\nLOCAL-EDIT (managed file modified locally):")
            for r in local_edit:
                print(f"  - {r['file']}")
        if missing:
            print("\nMISSING (file deleted locally):")
            for r in missing:
                print(f"  - {r['file']}")

    has_issues = any(r["status"] != "CURRENT" for r in results)
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
