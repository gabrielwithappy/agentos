from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / ".agents/skills/harness/writing-plans/scripts/review_artifacts.py"


def _module():
    spec = importlib.util.spec_from_file_location("review_artifacts", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_plan(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Example plan",
                "> **상태:** 진행 중<br>",
                "> reviewed: true<br>",
                "> implementation_started_at: <br>",
                "",
                "**목표:** 원래 목표",
                "",
                "## 진행 스냅샷",
                "| 전체 상태 | 진행 중 |",
                "",
                "## Task 1",
                "- [ ] 핵심 작업",
                "  Run: `true`",
                "  Expected: PASS",
                "",
                "## 구현 결과",
                "초기 결과",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _record_default_reviews(review, root: Path) -> None:
    for role, reviewer_id in (
        ("plan-reviewer", "independent-plan-reviewer"),
        ("principle-auditor", "independent-principle-auditor"),
    ):
        review.record_review(
            root,
            "plan.md",
            role,
            "PASS" if role == "plan-reviewer" else "PASS/CLEAN",
            reviewer_id,
            "subagent",
            "scope reviewed",
            "implementer",
        )


def test_metadata_only_changes_keep_new_artifact_valid(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)

    _record_default_reviews(review, tmp_path)
    text = plan.read_text(encoding="utf-8")
    text = text.replace("> **상태:** 진행 중<br>", "> **상태:** 완료<br>")
    text = text.replace("> implementation_started_at: <br>", "> implementation_started_at: now<br>")
    text = text.replace("- [ ] 핵심 작업", "- [x] 핵심 작업")
    text = text.replace("초기 결과", "갱신된 closeout 결과")
    plan.write_text(text, encoding="utf-8")

    result = review.check_plan(tmp_path, "plan.md")
    assert result.valid
    assert result.invalid == {}


def test_reviewed_state_transition_keeps_artifact_valid(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    plan.write_text(plan.read_text(encoding="utf-8").replace("> reviewed: true", "> reviewed: false"), encoding="utf-8")
    _record_default_reviews(review, tmp_path)
    plan.write_text(plan.read_text(encoding="utf-8").replace("> reviewed: false", "> reviewed: true"), encoding="utf-8")
    assert review.check_plan(tmp_path, "plan.md").valid


def test_usability_metadata_accepts_canonical_and_legacy_forms():
    review = _module()
    assert review.required_reviewers_for_text("> **usability_review_required:** true<br>\n")[-1] == "usability-reviewer"
    assert review.required_reviewers_for_text("> usability_review_required: true<br>\n")[-1] == "usability-reviewer"
    assert review.required_reviewers_for_text("> **usability_review_required:** false<br>\n") == ["plan-reviewer", "principle-auditor"]


def test_semantic_change_requires_new_review(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    _record_default_reviews(review, tmp_path)
    plan.write_text(
        plan.read_text(encoding="utf-8").replace("원래 목표", "변경된 목표"),
        encoding="utf-8",
    )

    result = review.check_plan(tmp_path, "plan.md")
    assert not result.valid
    assert result.invalid["plan-reviewer"] == "semantic-snapshot-mismatch"


def test_legacy_artifact_without_implementer_is_rejected(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    artifact_dir = tmp_path / ".agents/traces/reviews/plan"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "plan-reviewer.json").write_text(
        json.dumps(
            {
                "schema": "gate2-review-artifact-v1",
                "plan_path": "plan.md",
                "plan_sha256": "old-full-plan-hash",
                "reviewer_role": "plan-reviewer",
                "result": "PASS",
                "reviewer_id": "legacy-reviewer",
                "reviewer_source": "legacy",
                "summary": "legacy review",
                "reviewed_at": "2026-08-31T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "principle-auditor.json").write_text(
        json.dumps(
            {
                "schema": "gate2-review-artifact-v1",
                "plan_path": "plan.md",
                "reviewer_role": "principle-auditor",
                "result": "PASS/CLEAN",
                "reviewer_id": "legacy-principle",
                "reviewer_source": "legacy",
                "summary": "legacy audit",
                "reviewed_at": "2026-08-31T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    plan.write_text(plan.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    result = review.check_plan(tmp_path, "plan.md")
    assert not result.valid
    assert result.invalid["plan-reviewer"] == "missing-implementer-id"



def test_semantic_revision_increments_only_on_snapshot_change(tmp_path: Path, capsys):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    
    # Record first review
    out_path1 = review.record_review(
        tmp_path, "plan.md", "plan-reviewer", "PASS", "rev1", "subagent", "first", "imp"
    )
    artifact1 = review._load_artifact(out_path1)
    assert artifact1["semantic_revision"] == 1
    
    # Record second review without semantic change
    out_path2 = review.record_review(
        tmp_path, "plan.md", "plan-reviewer", "PASS", "rev2", "subagent", "second", "imp"
    )
    artifact2 = review._load_artifact(out_path2)
    assert artifact2["semantic_revision"] == 1
    
    # Change semantic content and record
    text = plan.read_text(encoding="utf-8")
    plan.write_text(text.replace("원래 목표", "변경된 목표"), encoding="utf-8")
    
    out_path3 = review.record_review(
        tmp_path, "plan.md", "plan-reviewer", "PASS", "rev3", "subagent", "third", "imp"
    )
    artifact3 = review._load_artifact(out_path3)
    assert artifact3["semantic_revision"] == 2

def test_approval_pending_output_for_missing_artifact(tmp_path: Path, monkeypatch, capsys):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    
    import sys
    monkeypatch.setattr(sys, "argv", ["review_artifacts.py", "check", "--plan", "plan.md", "--root", str(tmp_path)])
    
    try:
        review.main()
    except SystemExit as e:
        assert e.code == 1
        
    captured = capsys.readouterr()
    assert "APPROVAL_PENDING gate2-review-check" in captured.out


def test_record_fail_artifact_preserves_findings(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    findings = [
        {
            "id": "F-001",
            "severity": "blocking",
            "finding": "Missing preflight",
            "recovery": "Add preflight",
            "rereview": "Check preflight",
        }
    ]
    out_path = review.record_review(
        tmp_path,
        "plan.md",
        "plan-reviewer",
        "FAIL",
        "rev-1",
        "subagent",
        "failed review",
        "implementer",
        findings=findings,
    )
    loaded = review._load_artifact(out_path)
    assert loaded["result"] == "FAIL"
    assert loaded["findings"] == findings


def test_fail_artifact_is_non_approving(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    findings = [
        {
            "id": "F-001",
            "severity": "blocking",
            "finding": "issue",
            "recovery": "fix",
            "rereview": "verify",
        }
    ]
    review.record_review(
        tmp_path,
        "plan.md",
        "plan-reviewer",
        "FAIL",
        "rev-1",
        "subagent",
        "failed review",
        "implementer",
        findings=findings,
    )
    result = review.check_plan(tmp_path, "plan.md")
    assert not result.valid
    assert result.invalid.get("plan-reviewer") in {"result-failed", "result-not-pass"}


def test_complete_pass_sequence_is_approving(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    _write_plan(plan)
    _record_default_reviews(review, tmp_path)
    result = review.check_plan(tmp_path, "plan.md")
    assert result.valid


def _setup_closeout_plan(tmp_path: Path):
    plan = tmp_path / "plan.md"
    plan.write_text(
        "\n".join(
            [
                "# Plan",
                "> **상태:** 진행 중<br>",
                "> reviewed: true<br>",
                "- declared protected paths: `.agents/agents/harness/plan-reviewer.md`",
                "",
                "## 구현 결과",
                "변경 파일: `.agents/agents/harness/plan-reviewer.md` 가 성공적으로 구현되었습니다.",
                "",
                "## 사용 방법",
                "실행 명령: `python3 --version`",
                "",
                "## 완료 증거",
                "검증 명령: `python3 -c 'print(\"PASS\")'` 검증 결과: PASS review_artifacts.py run_harness_tests.sh",
                "",
                "## 아카이브 결정",
                "사용자 요청 시까지 active에 유지하고 archive --status 완료를 수행한다.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return plan


def test_closeout_accepts_concrete_result(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": review.plan_hash(plan.read_text(encoding="utf-8")),
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": [".agents/agents/harness/plan-reviewer.md"],
        "usage_command": "python3 --version",
        "usage_exit_code": 0,
        "verifiers": [{"command": "pytest", "exit_code": 0, "result": "PASS"}],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 0


def test_closeout_rejects_filler(tmp_path: Path):
    review = _module()
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n## 구현 결과\n(구현 후 작성)\n", encoding="utf-8")
    receipt_file = tmp_path / "receipt.json"
    receipt_file.write_text(json.dumps({"schema": "closeout-verification-v1"}), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1


def test_closeout_rejects_missing_usage(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": review.plan_hash(plan.read_text(encoding="utf-8")),
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": [".agents/agents/harness/plan-reviewer.md"],
        "usage_command": "",
        "usage_exit_code": 1,
        "verifiers": [{"command": "pytest", "exit_code": 0, "result": "PASS"}],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1


def test_closeout_rejects_missing_fresh(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": review.plan_hash(plan.read_text(encoding="utf-8")),
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": [".agents/agents/harness/plan-reviewer.md"],
        "usage_command": "python3 --version",
        "usage_exit_code": 0,
        "verifiers": [{"command": "pytest", "exit_code": 1, "result": "FAIL"}],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1


def test_closeout_rejects_stale_receipt(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": "stale-hash",
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": [".agents/agents/harness/plan-reviewer.md"],
        "usage_command": "python3 --version",
        "usage_exit_code": 0,
        "verifiers": [{"command": "pytest", "exit_code": 0, "result": "PASS"}],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1


def test_closeout_rejects_unscoped_changed_path(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": review.plan_hash(plan.read_text(encoding="utf-8")),
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": ["some/unscoped/file.py"],
        "usage_command": "python3 --version",
        "usage_exit_code": 0,
        "verifiers": [{"command": "pytest", "exit_code": 0, "result": "PASS"}],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1


def test_receipt_requires_all_verifiers(tmp_path: Path):
    review = _module()
    plan = _setup_closeout_plan(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": "plan.md",
        "plan_sha256": review.plan_hash(plan.read_text(encoding="utf-8")),
        "generated_at": "2026-09-04T00:00:00Z",
        "changed_paths": [".agents/agents/harness/plan-reviewer.md"],
        "usage_command": "python3 --version",
        "usage_exit_code": 0,
        "verifiers": [],
    }
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    assert review.closeout_check(tmp_path, "plan.md", "receipt.json") == 1
