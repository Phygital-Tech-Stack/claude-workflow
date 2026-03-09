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
    parser.add_argument("--preserve-existing", action="store_true",
                        help="Preserve project-specific servers from existing .mcp.json")
    args = parser.parse_args()

    # Collect template server names to know which are master-managed
    template_server_names = set()
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
            template_server_names.add(name)
            merged_servers[name] = config

    # Preserve project-specific servers from existing .mcp.json
    if args.preserve_existing and os.path.exists(args.output):
        try:
            with open(args.output) as f:
                existing = json.load(f)
            for name, config in existing.get("mcpServers", {}).items():
                if name not in template_server_names:
                    merged_servers[name] = config
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Could not parse existing {args.output}: {e}", file=sys.stderr)
            print("  Project-specific servers will not be preserved.", file=sys.stderr)

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
