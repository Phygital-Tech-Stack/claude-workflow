#!/usr/bin/env python3
"""Analyze .claude/compaction.log and print a summary report."""

import argparse
import re
import sys
from pathlib import Path


def parse_log(log_path: Path) -> list[dict]:
    """Parse compaction log entries."""
    entries = []
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})\S*\s+.*?(\d+)%")
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.search(line)
        if m:
            entries.append({"timestamp": m.group(1), "percent": int(m.group(2))})
    return entries


def main():
    parser = argparse.ArgumentParser(description="Compaction log summary")
    parser.add_argument(
        "--log",
        default=".claude/compaction.log",
        help="Path to compaction.log (default: .claude/compaction.log)",
    )
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"No compaction log found at {log_path}")
        sys.exit(0)

    entries = parse_log(log_path)
    if not entries:
        print("Compaction log exists but contains no parseable entries.")
        sys.exit(0)

    percentages = [e["percent"] for e in entries]
    avg = sum(percentages) / len(percentages)

    print(f"Compaction Report ({log_path})")
    print(f"  Total compactions:  {len(entries)}")
    print(f"  Avg context at compact: {avg:.0f}%")
    print(f"  Min / Max:          {min(percentages)}% / {max(percentages)}%")
    print(f"  Most recent:        {entries[-1]['timestamp']} at {entries[-1]['percent']}%")


if __name__ == "__main__":
    main()
