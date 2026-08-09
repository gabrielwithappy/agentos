import json
import os
import subprocess
from pathlib import Path
import pytest

@pytest.fixture
def workspace(tmp_path):
    os.chdir(tmp_path)
    (tmp_path / ".agents" / "hooks" / "scripts").mkdir(parents=True)
    source = Path("/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/hooks/scripts/stop_review_gate.py")
    if source.exists():
        (tmp_path / ".agents" / "hooks" / "scripts" / "stop_review_gate.py").symlink_to(source)
    active_dir = tmp_path / ".agentos" / "project" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path)
    yield tmp_path

def run_hook(cwd: Path, payload: dict) -> dict:
    hook_script = Path("/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/hooks/scripts/stop_review_gate.py")
    res = subprocess.run(
        ["python3", str(hook_script)],
        input=json.dumps(payload),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    return json.loads(res.stdout)

def test_invalid_review_warns_and_continues(workspace):
    plan = workspace / ".agentos" / "project" / "exec-plans" / "active" / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    payload = {"cwd": str(workspace), "last_assistant_message": "doing stuff"}
    res = run_hook(workspace, payload)
    assert res.get("continue") is True
    assert "warnings" in res
    warn = res["warnings"][0]
    assert warn["code"] == "review-evidence-invalid"

def test_valid_review_has_no_warning(workspace):
    import sys
    sys.path.insert(0, "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")
    import review_artifacts
    plan = workspace / ".agentos" / "project" / "exec-plans" / "active" / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    review_artifacts.record_review(
        root=workspace, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    review_artifacts.record_review(
        root=workspace, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="principle-auditor", result="PASS",
        reviewer_id="rev2", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    payload = {"cwd": str(workspace), "last_assistant_message": "doing stuff"}
    res = run_hook(workspace, payload)
    assert res.get("continue") is True
    assert "warnings" not in res

def test_malformed_artifact_is_redacted_invalid(workspace):
    import sys
    sys.path.insert(0, "/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")
    import review_artifacts
    plan = workspace / ".agentos" / "project" / "exec-plans" / "active" / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    review_artifacts.record_review(
        root=workspace, plan_path=".agentos/project/exec-plans/active/plan.md", reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    art_path = workspace / ".agents" / "traces" / "reviews" / "plan" / "principle-auditor.json"
    art_path.write_text("{malformed: true, secret: 'S3CR3T'}")
    payload = {"cwd": str(workspace), "last_assistant_message": "doing stuff"}
    res = run_hook(workspace, payload)
    assert res.get("continue") is True
    warn = res["warnings"][0]
    assert "S3CR3T" not in warn["detail"]
    assert "artifact-malformed" in warn["detail"]

def test_warning_does_not_mutate_plan_or_artifacts(workspace):
    plan = workspace / ".agentos" / "project" / "exec-plans" / "active" / "plan.md"
    plan.write_text("> reviewed: true\n\nsome plan")
    orig_stat = plan.stat()
    payload = {"cwd": str(workspace), "last_assistant_message": "doing stuff"}
    run_hook(workspace, payload)
    assert plan.stat().st_mtime == orig_stat.st_mtime

def test_warning_redacts_artifact_content(workspace):
    pass

def test_loop_lock_blocks(workspace):
    traces = workspace / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text("execution_locked: true")
    payload = {"cwd": str(workspace), "last_assistant_message": "doing stuff"}
    res = run_hook(workspace, payload)
    assert res.get("decision") == "block"

def test_unverified_completion_blocks(workspace):
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=workspace)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=workspace)
    (workspace / "dirty").write_text("dirty")
    subprocess.run(["git", "add", "dirty"], cwd=workspace)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace)
    (workspace / "dirty").write_text("dirty2")
    payload = {"cwd": str(workspace), "last_assistant_message": "I finished it."}
    res = run_hook(workspace, payload)
    assert res.get("decision") == "block"

def test_malformed_payload_continues(workspace):
    hook_script = Path("/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/hooks/scripts/stop_review_gate.py")
    res = subprocess.run(
        ["python3", str(hook_script)],
        input="{malformed_json}",
        cwd=workspace,
        capture_output=True,
        text=True,
    )
    out = json.loads(res.stdout)
    assert out.get("continue") is True
