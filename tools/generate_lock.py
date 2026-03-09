#!/usr/bin/env python3
"""Generate workflow.lock with both local and master source checksums.

The lock tracks two sets of hashes:
- managed: checksums of local files (after placeholder resolution + formatting)
- masterChecksums: checksums of raw master source files (pre-resolution)

This enables drift detection even when projects apply local formatters
(e.g., prettier) that modify files after init/sync.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

from workflow_utils import find_master_source, sha256_file


def main():
    parser = argparse.ArgumentParser(description="Generate workflow.lock")
    parser.add_argument("--claude-dir", required=True)
    parser.add_argument("--master-dir", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--stacks", required=True)
    args = parser.parse_args()

    claude_dir = args.claude_dir
    master_dir = args.master_dir
    version = args.version
    stacks = [s.strip() for s in args.stacks.split(",") if s.strip()]

    managed = {}
    master_checksums = {}

    for root, dirs, files in os.walk(claude_dir):
        # Skip __pycache__ and other non-content directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            # Skip compiled/cache files
            if fname.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, claude_dir)
            # Skip project-owned files
            if rel.startswith((
                "agent-memory/", "progress/", "session-files",
                "decisions.log", "compaction.log",
            )):
                continue
            if rel in ("settings.local.json", "project-rules.txt"):
                continue
            managed[rel] = sha256_file(full)

            # Find and hash the raw master source
            master_path = find_master_source(master_dir, rel, stacks)
            if master_path and os.path.exists(master_path):
                master_checksums[rel] = sha256_file(master_path)

    lock = {
        "version": version,
        "stacks": stacks,
        "lastSync": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "managed": managed,
        "masterChecksums": master_checksums,
    }

    lock_path = os.path.join(claude_dir, "workflow.lock")
    with open(lock_path, "w") as f:
        json.dump(lock, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
