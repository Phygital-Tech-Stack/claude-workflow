#!/usr/bin/env python3
"""Three-way checksum drift detection between project and master."""
import argparse
import hashlib
import json
import os
import sys

from workflow_utils import find_master_source, load_commands, sha256_file


def sha256_resolved(path: str, commands: dict[str, str]) -> str:
    """Hash a file after resolving {{PLACEHOLDER}} values."""
    with open(path, "r") as f:
        content = f.read()
    for key, val in commands.items():
        content = content.replace("{{" + key + "}}", val)
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


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

    # Self-mode: symlinks to base/ — just verify symlinks exist
    if lock.get("self"):
        results = []
        for rel_path in lock.get("managed", {}):
            if rel_path == "workflow.lock":
                continue
            local_path = os.path.join(claude_dir, rel_path)
            if not os.path.exists(local_path):
                results.append({"file": rel_path, "status": "MISSING"})
            elif os.path.islink(local_path):
                results.append({"file": rel_path, "status": "CURRENT"})
            else:
                # Regular file (not a symlink) — still valid, just not linked
                results.append({"file": rel_path, "status": "CURRENT"})

        if args.format == "json":
            print(json.dumps({"version": lock.get("version"), "self": True, "results": results}, indent=2))
        else:
            missing = [r for r in results if r["status"] == "MISSING"]
            current = [r for r in results if r["status"] == "CURRENT"]
            print(f"Workflow Drift Report (self-mode, v{lock.get('version')})")
            print(f"  CURRENT:    {len(current)} files")
            print(f"  MISSING:    {len(missing)} files")
            if missing:
                print("\nMISSING:")
                for r in missing:
                    print(f"  - {r['file']}")
        sys.exit(1 if any(r["status"] != "CURRENT" for r in results) else 0)

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

        local_hash = sha256_file(local_path)

        # Detect master changes using masterChecksums from the lock.
        # This avoids false drift when local formatters (e.g., prettier)
        # modify files after init/sync — we compare master-to-master
        # (raw source hash at sync time vs raw source hash now).
        if rel_path in master_checksums and master_exists:
            # Compare raw master source hash at sync time vs current.
            # masterChecksums stores raw (pre-resolution) hashes, so we
            # compare raw-to-raw to avoid false drift from local formatters.
            current_master_hash = sha256_file(master_path)
            master_changed = master_checksums[rel_path] != current_master_hash
        elif master_exists:
            # Fallback for locks without masterChecksums (pre-upgrade)
            if master_path.endswith(".md") and commands:
                master_hash = sha256_resolved(master_path, commands)
            else:
                master_hash = sha256_file(master_path)
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

    # Detect NEW files in master that aren't in the lock yet
    managed = set(lock.get("managed", {}).keys())

    def is_excluded(rel_path: str) -> bool:
        return any(rel_path.startswith(ex.rstrip("/")) for ex in excludes)

    # Scan base directories for untracked files
    scan_dirs = {
        "base/hooks": "hooks",
        "base/agents": "agents",
        "base/skills": "skills",
        "base/blueprints": "blueprints",
        "base/teams": "teams",
    }

    # Check WORKFLOW.md
    base_wf = os.path.join(args.master, "base", "WORKFLOW.md")
    if os.path.exists(base_wf) and "WORKFLOW.md" not in managed and not is_excluded("WORKFLOW.md"):
        results.append({"file": "WORKFLOW.md", "status": "NEW"})

    for src_dir_rel, dest_prefix in scan_dirs.items():
        src_dir = os.path.join(args.master, src_dir_rel)
        if not os.path.isdir(src_dir):
            continue
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fname in files:
                if fname.endswith((".pyc", ".pyo")):
                    continue
                src_path = os.path.join(root, fname)
                rel_from_src = os.path.relpath(src_path, src_dir)
                dest_rel = os.path.join(dest_prefix, rel_from_src)
                if dest_rel not in managed and not is_excluded(dest_rel):
                    results.append({"file": dest_rel, "status": "NEW"})

    # Scan stack directories for untracked files
    for stack in stacks:
        stack = stack.strip()
        if not stack:
            continue
        for sub in ("hooks", "failure-patterns"):
            src_dir = os.path.join(args.master, "stacks", stack, sub)
            if not os.path.isdir(src_dir):
                continue
            dest_prefix = "hooks" if sub == "hooks" else "hooks/failure-patterns"
            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fname in files:
                    if fname.endswith((".pyc", ".pyo")):
                        continue
                    src_path = os.path.join(root, fname)
                    if sub == "failure-patterns":
                        dest_rel = os.path.join(dest_prefix, fname)
                    else:
                        rel_from_src = os.path.relpath(src_path, src_dir)
                        dest_rel = os.path.join(dest_prefix, rel_from_src)
                    if dest_rel not in managed and not is_excluded(dest_rel):
                        results.append({"file": dest_rel, "status": "NEW"})

        # Scan stack teams
        teams_dir = os.path.join(args.master, "stacks", stack, "teams")
        if os.path.isdir(teams_dir):
            for root, dirs, files in os.walk(teams_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fname in files:
                    if fname.endswith((".pyc", ".pyo")):
                        continue
                    src_path = os.path.join(root, fname)
                    rel_from_teams = os.path.relpath(src_path, teams_dir)
                    dest_rel = os.path.join("teams", rel_from_teams)
                    if dest_rel not in managed and not is_excluded(dest_rel):
                        results.append({"file": dest_rel, "status": "NEW"})

    # Output
    if args.format == "json":
        print(json.dumps({"version": lock.get("version"), "results": results}, indent=2))
    else:
        behind = [r for r in results if r["status"] == "BEHIND"]
        diverged = [r for r in results if r["status"] == "DIVERGED"]
        local_edit = [r for r in results if r["status"] == "LOCAL-EDIT"]
        current = [r for r in results if r["status"] == "CURRENT"]
        missing = [r for r in results if r["status"] == "MISSING"]
        new = [r for r in results if r["status"] == "NEW"]

        print(f"Workflow Drift Report (pinned: v{lock.get('version')})")
        print(f"  CURRENT:    {len(current)} files")
        print(f"  BEHIND:     {len(behind)} files")
        print(f"  DIVERGED:   {len(diverged)} files")
        print(f"  LOCAL-EDIT: {len(local_edit)} files")
        print(f"  MISSING:    {len(missing)} files")
        print(f"  NEW:        {len(new)} files")

        if behind:
            print("\nBEHIND (auto-update available):")
            for r in behind:
                print(f"  - {r['file']}")
        if new:
            print("\nNEW (available in master, not yet synced):")
            for r in new:
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

    has_issues = any(r["status"] not in ("CURRENT",) for r in results)
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
