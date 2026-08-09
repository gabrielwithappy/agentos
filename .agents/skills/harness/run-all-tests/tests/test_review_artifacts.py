import json
from pathlib import Path
import pytest
import sys

sys.path.insert(0, "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")
import review_artifacts

def test_malformed_artifact_normalization(tmp_path):
    root = tmp_path
    active_dir = root / ".agentos" / "project" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    plan = active_dir / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    review_dir = root / ".agents" / "traces" / "reviews" / "plan"
    review_dir.mkdir(parents=True)
    review_artifacts.record_review(
        root=root, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    (review_dir / "principle-auditor.json").write_text("{malformed, secret: 'hello'}")
    res = review_artifacts.check_plan(root, ".agentos/project/exec-plans/active/plan.md")
    assert not res.valid
    assert "principle-auditor" in res.invalid
    assert res.invalid["principle-auditor"] == "artifact-malformed"
    assert "hello" not in str(res.to_dict())
