#!/usr/bin/env python3
"""Tests for drift_check.py JSON output."""
import json
import os
import shutil
import subprocess
import tempfile

MASTER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_mock_project():
    """Initialize a mock project and return its path."""
    project_dir = tempfile.mkdtemp()
    subprocess.run(
        [
            os.path.join(MASTER_DIR, "tools", "init.sh"),
            "--project", project_dir,
            "--stacks", "python-fastapi",
            "--master", MASTER_DIR,
        ],
        check=True,
        capture_output=True,
    )
    return project_dir


def run_drift_json(project_dir):
    """Run drift check and return parsed JSON."""
    result = subprocess.run(
        [
            os.path.join(MASTER_DIR, "tools", "diff.sh"),
            "--project", project_dir,
            "--master", MASTER_DIR,
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_local_edit_includes_master_source():
    """LOCAL-EDIT results must include master_source field."""
    project_dir = setup_mock_project()
    try:
        # Create a local edit
        workflow_path = os.path.join(project_dir, ".claude", "WORKFLOW.md")
        with open(workflow_path, "a") as f:
            f.write("\n# Local improvement\n")

        data = run_drift_json(project_dir)
        local_edits = [r for r in data["results"] if r["status"] == "LOCAL-EDIT"]

        assert len(local_edits) > 0, "Should have at least one LOCAL-EDIT"
        for r in local_edits:
            assert "master_source" in r, f"LOCAL-EDIT result missing master_source: {r}"
            assert r["master_source"] is not None, f"master_source should not be None for {r['file']}"
            # master_source should be a relative path like "base/WORKFLOW.md"
            assert r["master_source"].startswith(("base/", "stacks/")), \
                f"master_source should start with base/ or stacks/: {r['master_source']}"
    finally:
        shutil.rmtree(project_dir)


def test_current_files_no_master_source():
    """CURRENT results should not include master_source (saves bandwidth)."""
    project_dir = setup_mock_project()
    try:
        data = run_drift_json(project_dir)
        current = [r for r in data["results"] if r["status"] == "CURRENT"]
        assert len(current) > 0, "Should have CURRENT files"
        for r in current:
            assert "master_source" not in r or r.get("master_source") is None, \
                f"CURRENT files should not have master_source: {r}"
    finally:
        shutil.rmtree(project_dir)


if __name__ == "__main__":
    test_local_edit_includes_master_source()
    print("PASS: test_local_edit_includes_master_source")
    test_current_files_no_master_source()
    print("PASS: test_current_files_no_master_source")
    print("\nALL TESTS PASSED")
