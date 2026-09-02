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


def test_protected_approval_scope_requires_every_declared_file():
    review = _module()
    complete = set(review.PROTECTED_REVIEW_SCOPE)
    assert review.protected_scope_is_complete(complete)
    complete.remove("manifest update")
    assert not review.protected_scope_is_complete(complete)
