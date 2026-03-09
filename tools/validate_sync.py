#!/usr/bin/env python3
"""Post-sync validation — catches issues before commit/push.

Runs automatically as the last step in sync_all.sh, after init/sync but
before git add/commit. Exits non-zero on any BLOCK finding to prevent
pushing broken PRs.

Checks:
  1. Duplicate hooks (same command appearing twice)
  2. Unresolved {{PLACEHOLDER}} in managed files
  3. Non-executable .sh files in .claude/hooks/
  4. Permissions/MCP servers not lost vs original settings
  5. __pycache__ / .pyc in workflow.lock
  6. Credential patterns in staged files
  7. workflow.lock version matches expected
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


class SyncValidator:
    def __init__(self, claude_dir: str, original_settings: str | None = None,
                 expected_version: str | None = None):
        self.claude_dir = Path(claude_dir)
        self.original_settings = original_settings
        self.expected_version = expected_version
        self.blocks: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []

    def block(self, msg: str):
        self.blocks.append(msg)

    def warn(self, msg: str):
        self.warns.append(msg)

    def info(self, msg: str):
        self.infos.append(msg)

    # ── Check 1: Duplicate hooks ──────────────────────────────────────────

    def check_duplicate_hooks(self):
        settings_path = self.claude_dir / "settings.json"
        if not settings_path.exists():
            self.block("settings.json missing")
            return

        with open(settings_path) as f:
            settings = json.load(f)

        hooks = settings.get("hooks", {})
        for event_key, groups in hooks.items():
            seen: dict[str, int] = {}  # hash -> group index
            for i, group in enumerate(groups):
                for hook in group.get("hooks", []):
                    cmd = hook.get("command", "") or hook.get("prompt", "") or hook.get("agent", "")
                    if not cmd:
                        continue
                    h = hashlib.md5(cmd.encode()).hexdigest()[:12]
                    if h in seen:
                        short = cmd.replace("\n", " ")[:80]
                        self.block(
                            f"Duplicate hook in {event_key}: groups [{seen[h]}] and [{i}] "
                            f"have identical command: {short}..."
                        )
                    else:
                        seen[h] = i

    # ── Check 2: Unresolved placeholders ──────────────────────────────────

    def check_unresolved_placeholders(self):
        placeholder_re = re.compile(r"\{\{([A-Z_]+)\}\}")
        # Only check managed files, not project-specific ones
        skip_dirs = {"agent-memory", "progress", "__pycache__"}
        skip_files = {"settings.local.json", "project-rules.txt"}

        for root, dirs, files in os.walk(self.claude_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if fname in skip_files or fname.endswith((".pyc", ".pyo")):
                    continue
                full = Path(root) / fname
                rel = full.relative_to(self.claude_dir)

                # Only check text files
                if fname.endswith((".sh", ".md", ".json", ".yaml", ".yml", ".txt")):
                    try:
                        content = full.read_text(errors="replace")
                    except Exception:
                        continue
                    matches = placeholder_re.findall(content)
                    for m in matches:
                        # SCREENSHOT_COMMAND in flutter-only docs is INFO, not BLOCK
                        if m == "SCREENSHOT_COMMAND":
                            self.info(f"{{{{SCREENSHOT_COMMAND}}}} unresolved in {rel} (flutter-only section)")
                        else:
                            self.block(f"{{{{{m}}}}} unresolved in {rel}")

    # ── Check 3: Hook file permissions ────────────────────────────────────

    def check_hook_permissions(self):
        hooks_dir = self.claude_dir / "hooks"
        if not hooks_dir.exists():
            self.block("hooks/ directory missing")
            return

        for sh_file in sorted(hooks_dir.glob("*.sh")):
            # Check filesystem permission
            if not os.access(sh_file, os.X_OK):
                self.warn(f"{sh_file.relative_to(self.claude_dir)} not executable on filesystem")

            # Check git index permission (more important — this is what gets committed)
            try:
                result = subprocess.run(
                    ["git", "ls-files", "-s", str(sh_file.relative_to(Path.cwd()))],
                    capture_output=True, text=True, cwd=self.claude_dir.parent
                )
                if result.stdout:
                    mode = result.stdout.split()[0]
                    if mode != "100755":
                        self.block(
                            f"{sh_file.relative_to(self.claude_dir)} has git mode {mode} "
                            f"(should be 100755)"
                        )
            except Exception:
                pass  # git not available or file not staged yet

    # ── Check 4: Permissions / MCP servers preserved ──────────────────────

    def check_preserved_settings(self):
        if not self.original_settings or not os.path.exists(self.original_settings):
            return

        settings_path = self.claude_dir / "settings.json"
        if not settings_path.exists():
            return

        with open(self.original_settings) as f:
            original = json.load(f)
        with open(settings_path) as f:
            current = json.load(f)

        # Check permissions
        orig_perms = original.get("permissions", {})
        curr_perms = current.get("permissions", {})
        if orig_perms:
            for key in ("allow", "deny"):
                orig_list = set(orig_perms.get(key, []))
                curr_list = set(curr_perms.get(key, []))
                lost = orig_list - curr_list
                if lost:
                    self.block(
                        f"Lost {len(lost)} permission {key} rules: "
                        f"{', '.join(sorted(lost)[:5])}{'...' if len(lost) > 5 else ''}"
                    )

        # Check MCP servers
        orig_mcp = set(original.get("enabledMcpjsonServers", []))
        curr_mcp = set(current.get("enabledMcpjsonServers", []))
        lost_mcp = orig_mcp - curr_mcp
        if lost_mcp:
            self.block(f"Lost MCP servers: {', '.join(sorted(lost_mcp))}")

    # ── Check 5: __pycache__ in workflow.lock ─────────────────────────────

    def check_lock_pycache(self):
        lock_path = self.claude_dir / "workflow.lock"
        if not lock_path.exists():
            self.block("workflow.lock missing")
            return

        with open(lock_path) as f:
            lock = json.load(f)

        managed = lock.get("managed", {})
        pycache_entries = [k for k in managed if "__pycache__" in k or k.endswith((".pyc", ".pyo"))]
        if pycache_entries:
            self.block(f"workflow.lock tracks bytecache: {', '.join(pycache_entries)}")

    # ── Check 6: Credential patterns ──────────────────────────────────────

    def check_credentials(self):
        # Check if .mcp.json is staged for commit (it shouldn't be)
        try:
            project_dir = self.claude_dir.parent
            result = subprocess.run(
                ["git", "ls-files", "--cached", ".mcp.json"],
                capture_output=True, text=True, cwd=project_dir
            )
            if result.stdout.strip():
                self.block(".mcp.json is tracked in git (may contain credentials)")
        except Exception:
            pass

        # Check settings.json for obvious credential patterns
        settings_path = self.claude_dir / "settings.json"
        if settings_path.exists():
            content = settings_path.read_text()
            cred_patterns = [
                (r'"password"\s*:', "password field"),
                (r'"secret"\s*:', "secret field"),
                (r'"token"\s*:\s*"[A-Za-z0-9+/=]{20,}"', "token value"),
                (r'redis://:[^@]+@', "Redis credentials"),
                (r'postgres://[^:]+:[^@]+@', "PostgreSQL credentials"),
                (r'mongodb://[^:]+:[^@]+@', "MongoDB credentials"),
            ]
            for pattern, desc in cred_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.block(f"Possible credentials in settings.json: {desc}")

    # ── Check 7: Lock version ─────────────────────────────────────────────

    def check_lock_version(self):
        if not self.expected_version:
            return

        lock_path = self.claude_dir / "workflow.lock"
        if not lock_path.exists():
            return

        with open(lock_path) as f:
            lock = json.load(f)

        actual = lock.get("version", "")
        if actual != self.expected_version:
            self.block(
                f"workflow.lock version is {actual!r}, expected {self.expected_version!r}"
            )

    # ── Check 8: Hook timeout sanity ──────────────────────────────────────

    def check_hook_timeouts(self):
        settings_path = self.claude_dir / "settings.json"
        if not settings_path.exists():
            return

        with open(settings_path) as f:
            settings = json.load(f)

        for event_key, groups in settings.get("hooks", {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    timeout = hook.get("timeout")
                    if timeout is not None and timeout > 300:
                        self.block(
                            f"Hook timeout {timeout}s in {event_key} is suspiciously high "
                            f"(>300s). Claude Code timeouts are in seconds, not milliseconds."
                        )

    # ── Run all checks ────────────────────────────────────────────────────

    def run(self) -> bool:
        """Run all checks. Returns True if no BLOCKs found."""
        self.check_duplicate_hooks()
        self.check_unresolved_placeholders()
        self.check_hook_permissions()
        self.check_preserved_settings()
        self.check_lock_pycache()
        self.check_credentials()
        self.check_lock_version()
        self.check_hook_timeouts()
        return len(self.blocks) == 0

    def print_report(self):
        total = len(self.blocks) + len(self.warns) + len(self.infos)
        if total == 0:
            print("  Validation: PASS (0 findings)")
            return

        if self.blocks:
            for finding in self.blocks:
                print(f"  BLOCK: {finding}")
        if self.warns:
            for finding in self.warns:
                print(f"  WARN:  {finding}")
        if self.infos:
            for finding in self.infos:
                print(f"  INFO:  {finding}")

        verdict = "FAIL" if self.blocks else "PASS"
        print(f"  Validation: {verdict} "
              f"({len(self.blocks)} BLOCK, {len(self.warns)} WARN, {len(self.infos)} INFO)")


def main():
    parser = argparse.ArgumentParser(description="Validate post-sync .claude/ directory")
    parser.add_argument("--claude-dir", required=True, help="Path to .claude directory")
    parser.add_argument("--original-settings", help="Path to original settings.json (pre-sync)")
    parser.add_argument("--expected-version", help="Expected workflow.lock version")
    args = parser.parse_args()

    validator = SyncValidator(
        claude_dir=args.claude_dir,
        original_settings=args.original_settings,
        expected_version=args.expected_version,
    )

    passed = validator.run()
    validator.print_report()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
