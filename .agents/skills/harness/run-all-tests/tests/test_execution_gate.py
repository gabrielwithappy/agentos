import subprocess
from pathlib import Path

def test_valid_review_artifact_allows_dispatch(tmp_path):
    import sys
    sys.path.insert(0, "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")
    import review_artifacts
    
    root = tmp_path
    active_dir = root / ".agentos" / "project" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    plan = active_dir / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    
    review_artifacts.record_review(
        root=root, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    review_artifacts.record_review(
        root=root, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="principle-auditor", result="PASS",
        reviewer_id="rev2", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    
    script = "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts/execution_gate.py"
    res = subprocess.run(["python3", script, "--plan", ".agentos/project/exec-plans/active/plan.md"], cwd=root)
    assert res.returncode == 0

def test_invalid_review_artifact_blocks_dispatch(tmp_path):
    root = tmp_path
    active_dir = root / ".agentos" / "project" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    plan = active_dir / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    
    script = "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts/execution_gate.py"
    res = subprocess.run(["python3", script, "--plan", ".agentos/project/exec-plans/active/plan.md"], cwd=root, capture_output=True, text=True)
    assert res.returncode == 2
    assert "FAIL execution-gate missing=plan-reviewer,principle-auditor" in res.stdout
    assert "recovery command: python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/plan.md" in res.stdout

def test_malformed_artifact_blocks_dispatch_without_leaking(tmp_path):
    import sys
    sys.path.insert(0, "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")
    import review_artifacts
    
    root = tmp_path
    active_dir = root / ".agentos" / "project" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    plan = active_dir / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    
    review_artifacts.record_review(
        root=root, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    
    review_dir = root / ".agents" / "traces" / "reviews" / "plan"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "principle-auditor.json").write_text("{secret: 'mysecret', malformed: true}")
    
    script = "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts/execution_gate.py"
    res = subprocess.run(["python3", script, "--plan", ".agentos/project/exec-plans/active/plan.md"], cwd=root, capture_output=True, text=True)
    assert res.returncode == 2
    assert "FAIL execution-gate invalid=principle-auditor" in res.stdout
    assert "mysecret" not in res.stdout
