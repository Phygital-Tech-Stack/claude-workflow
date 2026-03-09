#!/usr/bin/env python3
"""Merge .mcp.json.template files from stack directories and resolve tokens."""
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Merge MCP templates from stacks")
    parser.add_argument("--stacks", required=True, help="Comma-separated stack names")
    parser.add_argument("--stacks-dir", required=True, help="Path to stacks directory")
    parser.add_argument("--output", required=True, help="Output .mcp.json path")
    args = parser.parse_args()

    merged_servers = {}
    for stack in args.stacks.split(","):
        stack = stack.strip()
        if not stack:
            continue
        tmpl_path = os.path.join(args.stacks_dir, stack, ".mcp.json.template")
        if not os.path.exists(tmpl_path):
            continue
        with open(tmpl_path) as f:
            tmpl = json.load(f)
        for name, config in tmpl.get("mcpServers", {}).items():
            merged_servers[name] = config

    if not merged_servers:
        sys.exit(0)

    result = json.dumps({"mcpServers": merged_servers}, indent=2)

    # Resolve token placeholders from environment
    token_map = {
        "{{PHAROS_TOKEN}}": os.environ.get("PHAROS_TOKEN", ""),
        "{{GITHUB_TOKEN}}": os.environ.get(
            "GITHUB_TOKEN", os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        ),
    }
    unresolved = []
    for placeholder, value in token_map.items():
        if placeholder in result:
            if value:
                result = result.replace(placeholder, value)
            else:
                unresolved.append(placeholder.strip("{}"))

    with open(args.output, "w") as f:
        f.write(result + "\n")

    count = len(merged_servers)
    print(f"Created {args.output} with {count} MCP server(s)", file=sys.stderr)
    if unresolved:
        print(
            f"WARNING: Unresolved tokens in {args.output}: {', '.join(unresolved)}. "
            f"Set the corresponding environment variables.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
