#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_DIR="$(dirname "$SCRIPT_DIR")"

# Setup
MOCK_PROJECT=$(mktemp -d)
mkdir -p "$MOCK_PROJECT/.claude"
trap "rm -rf $MOCK_PROJECT" EXIT

# Run init
"$MASTER_DIR/tools/init.sh" --project "$MOCK_PROJECT" --stacks typescript-nestjs --master "$MASTER_DIR"

# Assertions
assert_file_exists() { [ -f "$1" ] || { echo "FAIL: $1 not found"; exit 1; }; }
assert_dir_exists() { [ -d "$1" ] || { echo "FAIL: $1 not found"; exit 1; }; }
assert_contains() { grep -q "$2" "$1" || { echo "FAIL: $1 missing '$2'"; exit 1; }; }

# Core files
assert_file_exists "$MOCK_PROJECT/.claude/workflow.lock"
assert_file_exists "$MOCK_PROJECT/.claude/workflow.overrides.yaml"
assert_file_exists "$MOCK_PROJECT/.claude/WORKFLOW.md"

# Base hooks
assert_file_exists "$MOCK_PROJECT/.claude/hooks/session-start.sh"
assert_file_exists "$MOCK_PROJECT/.claude/hooks/pre-compact.sh"
assert_file_exists "$MOCK_PROJECT/.claude/hooks/post-failure.sh"
assert_file_exists "$MOCK_PROJECT/.claude/hooks/task-completed.sh"
assert_file_exists "$MOCK_PROJECT/.claude/hooks/subagent-start.sh"
assert_file_exists "$MOCK_PROJECT/.claude/hooks/teammate-idle.sh"

# Stack hooks
assert_file_exists "$MOCK_PROJECT/.claude/hooks/tdd-guard.sh"

# Skills
assert_dir_exists "$MOCK_PROJECT/.claude/skills/commit"
assert_dir_exists "$MOCK_PROJECT/.claude/skills/tdd"
assert_dir_exists "$MOCK_PROJECT/.claude/skills/validate-change"
assert_file_exists "$MOCK_PROJECT/.claude/skills/commit/SKILL.md"

# Agents
assert_file_exists "$MOCK_PROJECT/.claude/agents/code-reviewer.md"

# Blueprints
assert_file_exists "$MOCK_PROJECT/.claude/blueprints/coding-conventions.md"
assert_file_exists "$MOCK_PROJECT/.claude/blueprints/testing-patterns.md"

# Composed settings
assert_file_exists "$MOCK_PROJECT/.claude/settings.json"

# Failure patterns
assert_file_exists "$MOCK_PROJECT/.claude/hooks/failure-patterns/typescript.py"

# Lock file contents
assert_contains "$MOCK_PROJECT/.claude/workflow.lock" '"version"'
assert_contains "$MOCK_PROJECT/.claude/workflow.lock" '"managed"'

# Overrides file contents
assert_contains "$MOCK_PROJECT/.claude/workflow.overrides.yaml" "typescript-nestjs"

echo "ALL TESTS PASSED"
