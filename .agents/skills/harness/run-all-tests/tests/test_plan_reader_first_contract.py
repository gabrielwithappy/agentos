from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_writing_plan_template_requires_reader_first_sections():
    text = read(".agents/skills/harness/writing-plans/SKILL.md")

    assert "## 사용자 결과 요약" in text
    assert "## 사용자 진행 계획" in text
    assert "사용자가 무엇을 얻게 되는가?" in text
    assert "일상 사용에서 무엇이 달라지는가?" in text
    assert "사용자에게 보이는 결과" in text
    assert "한국어가 모국어인 사용자가 빠르게 이해" in text
    assert "presentation contract" in text
    assert "override" in text


def test_review_contract_rejects_missing_or_unsafe_reader_first_sections():
    checklist = read(".agents/skills/harness/writing-plans/plan-review-checklist.md")
    reviewer = read(".agents/agents/harness/plan-reviewer.md")
    usability = read(".agents/agents/harness/usability-reviewer.md")

    for text in (checklist, reviewer, usability):
        assert ("사용자 결과 요약" in text) or ("User Result Brief" in text)
        assert ("사용자 진행 계획" in text) or ("User Progress Plan" in text)
        assert ("한국어" in text) or ("Korean-first" in text)

    assert "too technical" in reviewer or "너무 기술 용어 중심" in reviewer
    assert "FAIL" in reviewer
    assert "prompt-injection data" in reviewer
    assert "protected-path" in usability
    assert "Gate 2 bypass" in usability


def test_executing_plans_updates_reader_first_progress_only_after_verification():
    text = read(".agents/skills/harness/executing-plans/SKILL.md")

    assert "Update `사용자 진행 계획` rows" in text
    assert "Never mark a `사용자 진행 계획` milestone complete" in text
    assert "verification signal exists" in text
    assert "Do not add a progress DB" in text


def test_korean_active_plans_have_reader_first_sections():
    active_dir = ROOT / ".agentos/project/exec-plans/active"
    plans = sorted(active_dir.glob("*.ko.md"))
    if not plans:
        return

    for plan in plans:
        text = plan.read_text(encoding="utf-8")
        assert ("## 사용자 결과 요약" in text) or ("## User Result Brief" in text), plan
        assert ("## 사용자 진행 계획" in text) or ("## User Progress Plan" in text), plan
        assert ("사용자가 무엇을 얻게 되는가?" in text) or ("What will the user get?" in text), plan
        assert ("사용자에게 보이는 결과" in text) or ("User-visible result" in text), plan


# Integration fixtures for unified hook and final adjudication: dispatch --stage final, final adjudication, plan-reviewer-final
import json
import importlib.util


def _load_alignment_module():
    spec = importlib.util.spec_from_file_location(
        "check_alignment",
        ROOT / ".agents/hooks/scripts/check-alignment.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setup_test_plan(tmp_path: Path):
    plan = tmp_path / ".agentos/project/exec-plans/active/plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        "# Test plan\n> **상태:** 진행 중\n> reviewed: true\n\n**목표:** 테스트\n",
        encoding="utf-8",
    )
    return plan


def test_first_handoff(tmp_path: Path, monkeypatch):
    plan = _setup_test_plan(tmp_path)
    monkeypatch.chdir(tmp_path)
    scripts_dir = ROOT / ".agents/skills/harness/writing-plans/scripts"
    import sys; sys.path.insert(0, str(scripts_dir))
    import review_artifacts as r
    digest = r.plan_hash(plan.read_text(encoding="utf-8"))
    review_dir = tmp_path / ".agents/traces/reviews/plan"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "plan-reviewer.json").write_text(json.dumps({
        "schema": "gate2-review-artifact-v1",
        "plan_path": ".agentos/project/exec-plans/active/plan.md",
        "plan_identity": ".agentos/project/exec-plans/active/plan.md",
        "review_scope": "gate2",
        "semantic_revision": 1,
        "semantic_snapshot": r.semantic_snapshot(plan.read_text(encoding="utf-8")),
        "plan_sha256": digest,
        "reviewer_role": "plan-reviewer",
        "result": "PASS",
        "reviewer_id": "reviewer-1",
        "reviewer_source": "subagent",
        "implementer_id": "codex",
        "summary": "pass",
        "reviewed_at": "2026-09-04T00:00:00Z",
        "triage_surface": ["core"],
        "required_reviewers": ["plan-reviewer", "principle-auditor"],
        "review_sequence": ["plan-reviewer", "principle-auditor"],
        "adjudication": "non-blocking",
        "blocking_findings": [],
        "required_follow_up": [],
    }), encoding="utf-8")
    assert r.dispatch(tmp_path, ".agentos/project/exec-plans/active/plan.md", "triage") == 0
    assert (review_dir / "plan-reviewer-handoff.json").is_file()


def test_missing_handoff(tmp_path: Path, monkeypatch):
    align = _load_alignment_module()
    plan = _setup_test_plan(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(align, "get_target_plans", lambda root: [str(plan.relative_to(tmp_path))])
    assert align.check_alignment() == 1


def test_downstream_only(tmp_path: Path, monkeypatch):
    align = _load_alignment_module()
    plan = _setup_test_plan(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(align, "get_target_plans", lambda root: [str(plan.relative_to(tmp_path))])
    review_dir = tmp_path / ".agents/traces/reviews/plan"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "principle-auditor.json").write_text(json.dumps({
        "schema": "gate2-review-artifact-v1",
        "plan_path": ".agentos/project/exec-plans/active/plan.md",
        "reviewer_role": "principle-auditor",
        "result": "PASS/CLEAN",
        "reviewer_id": "auditor-1",
        "reviewer_source": "subagent",
        "implementer_id": "codex",
        "summary": "pass",
        "reviewed_at": "2026-09-04T00:00:00Z",
    }), encoding="utf-8")
    assert align.check_alignment() == 1


def test_non_plan_reviewer_final_owner(tmp_path: Path, monkeypatch):
    align = _load_alignment_module()
    plan = _setup_test_plan(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(align, "get_target_plans", lambda root: [str(plan.relative_to(tmp_path))])
    review_dir = tmp_path / ".agents/traces/reviews/plan"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "plan-reviewer-handoff.json").write_text("{}", encoding="utf-8")
    (review_dir / "plan-reviewer-final.json").write_text(json.dumps({
        "final_adjudicator": "principle-auditor",
        "adjudication": "non-blocking",
    }), encoding="utf-8")
    assert align.check_alignment() == 1


def test_valid_final_handoff(tmp_path: Path, monkeypatch):
    align = _load_alignment_module()
    plan = _setup_test_plan(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(align, "get_target_plans", lambda root: [str(plan.relative_to(tmp_path))])
    scripts_dir = ROOT / ".agents/skills/harness/writing-plans/scripts"
    import sys; sys.path.insert(0, str(scripts_dir))
    import review_artifacts as r
    digest = r.plan_hash(plan.read_text(encoding="utf-8"))
    snapshot = r.semantic_snapshot(plan.read_text(encoding="utf-8"))
    review_dir = tmp_path / ".agents/traces/reviews/plan"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "plan-reviewer.json").write_text(json.dumps({
        "schema": "gate2-review-artifact-v1",
        "plan_path": ".agentos/project/exec-plans/active/plan.md",
        "plan_identity": ".agentos/project/exec-plans/active/plan.md",
        "review_scope": "gate2",
        "semantic_revision": 1,
        "semantic_snapshot": snapshot,
        "plan_sha256": digest,
        "reviewer_role": "plan-reviewer",
        "result": "PASS",
        "reviewer_id": "reviewer-1",
        "reviewer_source": "subagent",
        "implementer_id": "codex",
        "summary": "pass",
        "reviewed_at": "2026-09-04T00:00:00Z",
        "triage_surface": ["core"],
        "required_reviewers": ["plan-reviewer", "principle-auditor"],
        "review_sequence": ["plan-reviewer", "principle-auditor"],
        "adjudication": "non-blocking",
        "blocking_findings": [],
        "required_follow_up": [],
    }), encoding="utf-8")
    (review_dir / "principle-auditor.json").write_text(json.dumps({
        "schema": "gate2-review-artifact-v1",
        "plan_path": ".agentos/project/exec-plans/active/plan.md",
        "plan_identity": ".agentos/project/exec-plans/active/plan.md",
        "review_scope": "gate2",
        "semantic_revision": 1,
        "semantic_snapshot": snapshot,
        "plan_sha256": digest,
        "reviewer_role": "principle-auditor",
        "result": "PASS/CLEAN",
        "reviewer_id": "auditor-1",
        "reviewer_source": "subagent",
        "implementer_id": "codex",
        "summary": "pass",
        "reviewed_at": "2026-09-04T00:00:00Z",
        "depends_on": "plan-reviewer",
        "sequence": 2,
    }), encoding="utf-8")
    assert r.dispatch(tmp_path, ".agentos/project/exec-plans/active/plan.md", "triage") == 0
    (review_dir / "plan-reviewer-final.json").write_text(json.dumps({
        "final_adjudicator": "plan-reviewer",
        "adjudication": "non-blocking",
        "blocking_findings": [],
        "required_follow_up": [],
    }), encoding="utf-8")
    assert align.check_alignment() == 0
