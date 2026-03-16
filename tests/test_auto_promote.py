#!/usr/bin/env python3
"""Tests for auto_promote.py logic."""
import json
import os
import shutil
import subprocess
import tempfile

MASTER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_find_promote_candidates():
    """Should identify LOCAL-EDIT files that have a master source."""
    import sys
    sys.path.insert(0, os.path.join(MASTER_DIR, "tools"))
    from auto_promote import find_promote_candidates

    drift_data = {
        "version": "1.0.0",
        "results": [
            {"file": "WORKFLOW.md", "status": "CURRENT"},
            {"file": "skills/commit/SKILL.md", "status": "LOCAL-EDIT", "master_source": "base/skills/commit/SKILL.md"},
            {"file": "hooks/session-start.py", "status": "LOCAL-EDIT", "master_source": "base/hooks/session-start.py"},
            {"file": "hooks/ruff_format.sh", "status": "LOCAL-EDIT", "master_source": "stacks/python-fastapi/hooks/ruff_format.sh"},
            {"file": "settings.json", "status": "LOCAL-EDIT"},  # No master_source — composed file, skip
            {"file": "WORKFLOW.md", "status": "BEHIND"},
        ],
    }

    candidates = find_promote_candidates(drift_data)
    assert len(candidates) == 3, f"Expected 3 candidates, got {len(candidates)}"
    assert candidates[0]["file"] == "skills/commit/SKILL.md"
    assert candidates[0]["master_source"] == "base/skills/commit/SKILL.md"


def test_no_candidates_when_no_local_edits():
    """Should return empty list when no LOCAL-EDIT files exist."""
    import sys
    sys.path.insert(0, os.path.join(MASTER_DIR, "tools"))
    from auto_promote import find_promote_candidates

    drift_data = {
        "version": "1.0.0",
        "results": [
            {"file": "WORKFLOW.md", "status": "CURRENT"},
            {"file": "hooks/session-start.py", "status": "BEHIND"},
        ],
    }

    candidates = find_promote_candidates(drift_data)
    assert len(candidates) == 0


def test_generate_branch_name():
    """Branch name should be promote/<project>/<short-hash>."""
    import sys
    sys.path.insert(0, os.path.join(MASTER_DIR, "tools"))
    from auto_promote import generate_branch_name

    name = generate_branch_name("Phygital-Tech-Stack/erp")
    assert name.startswith("promote/erp/"), f"Expected promote/erp/..., got {name}"
    assert len(name) < 40, f"Branch name too long: {name}"


def test_generate_pr_body():
    """PR body should contain file table and project link."""
    import sys
    sys.path.insert(0, os.path.join(MASTER_DIR, "tools"))
    from auto_promote import generate_pr_body

    candidates = [
        {"file": "skills/commit/SKILL.md", "master_source": "base/skills/commit/SKILL.md"},
        {"file": "hooks/ruff_format.sh", "master_source": "stacks/python-fastapi/hooks/ruff_format.sh"},
    ]

    body = generate_pr_body("Phygital-Tech-Stack/erp", candidates)
    assert "Phygital-Tech-Stack/erp" in body
    assert "skills/commit/SKILL.md" in body
    assert "base/skills/commit/SKILL.md" in body
    assert "Review" in body or "review" in body


if __name__ == "__main__":
    test_find_promote_candidates()
    print("PASS: test_find_promote_candidates")
    test_no_candidates_when_no_local_edits()
    print("PASS: test_no_candidates_when_no_local_edits")
    test_generate_branch_name()
    print("PASS: test_generate_branch_name")
    test_generate_pr_body()
    print("PASS: test_generate_pr_body")
    print("\nALL TESTS PASSED")
