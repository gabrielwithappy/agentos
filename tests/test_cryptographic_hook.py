import os
import shutil
import tempfile
from pathlib import Path
import pytest

from agentos.observability.plan_parser import parse_exec_plan


def test_request_review_creates_secret_key_and_signed_review(tmp_path):
    # Setup test plan
    plan_dir = tmp_path / ".agentos" / "project" / "exec-plans" / "active"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "2026-07-31-test-hook.md"
    plan_file.write_text(
        "# Test Plan\n\n"
        "> **상태:** 구현 계획 (실행 대기)\n"
        "> reviewed: true<br>\n\n"
        "**목표:** Test cryptographic hook\n\n"
        "**사용자 결과:** Test outcome\n\n"
        "## 진행 스냅샷\n| 필드 | 현재 값 |\n|---|---|\n| 전체 상태 | 실행 대기 |\n",
        encoding="utf-8",
    )

    # Import scripts dynamically from harness
    import sys
    scripts_dir = Path(".agents/skills/harness/writing-plans/scripts").resolve()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from review_artifacts import record_review
    from request_review import create_signed_review, get_or_create_secret_key

    # Record mock reviews required for Gate 2
    record_review(
        root=tmp_path,
        plan_path=".agentos/project/exec-plans/active/2026-07-31-test-hook.md",
        reviewer="plan-reviewer",
        result="PASS",
        reviewer_id="rev-1",
        reviewer_source="subagent",
        summary="OK",
        implementer_id=None,
    )
    record_review(
        root=tmp_path,
        plan_path=".agentos/project/exec-plans/active/2026-07-31-test-hook.md",
        reviewer="principle-auditor",
        result="PASS",
        reviewer_id="rev-2",
        reviewer_source="subagent",
        summary="OK",
        implementer_id=None,
    )

    # Create signed review
    out_path = create_signed_review(tmp_path, ".agentos/project/exec-plans/active/2026-07-31-test-hook.md")
    assert out_path.is_file()

    secret_key_file = tmp_path / ".agentos" / "secret.key"
    assert secret_key_file.is_file()


def _load_check_alignment_module():
    import importlib.util

    path = Path(".agents/hooks/scripts/check-alignment.py").resolve()
    spec = importlib.util.spec_from_file_location("check_alignment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRE_CLOSEOUT_PLAN = """# Test Plan

> **상태:** 구현 계획 (실행 대기)<br>
> reviewed: true<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

**목표:** Test cryptographic hook

**사용자 결과:** Test outcome

## 진행 스냅샷
| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 실행 대기 |

### Task 1: 예시
- [ ] **Step 1:** do the thing

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 완료 증거
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
"""

# Same plan after a legitimate "Completed Active Plan Closeout" pass: only
# living fields/sections changed (timestamps, checkboxes, agent/session,
# dashboard id, and the closeout prose sections). 목표/사용자 결과/Task 본문
# are untouched.
POST_CLOSEOUT_PLAN = """# Test Plan

> **상태:** 완료<br>
> reviewed: true<br>
> active_agent: Claude Code<br>
> active_session: abc-123-def<br>
> dashboard_item_id: PVTI_example<br>
> implementation_started_at: 2026-08-01T01:00:00Z<br>
> implementation_completed_at: 2026-08-01T01:05:00Z<br>
> implementation_duration: 5m<br>

**목표:** Test cryptographic hook

**사용자 결과:** Test outcome

## 진행 스냅샷
| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |

### Task 1: 예시
- [x] **Step 1:** do the thing

## 구현 결과
- Did the thing successfully.

## 사용 방법
- Run `the-thing`.

## 완료 증거
- `pytest` -> 1 passed

## 아카이브 결정
- Not yet archived.
"""


def test_normalize_plan_text_stable_across_legitimate_closeout_edits():
    """Regression test for the bug this plan fixes: filling in the fields the
    'Completed Active Plan Closeout' contract (writing-plans/SKILL.md) requires
    after Gate 2 signing must not change the plan's signed hash, in either of
    the two duplicated normalize_plan_text() implementations."""
    import sys

    scripts_dir = Path(".agents/skills/harness/writing-plans/scripts").resolve()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import review_artifacts as ra

    ca = _load_check_alignment_module()

    for plan_hash in (ra.plan_hash, ca.plan_hash):
        assert plan_hash(PRE_CLOSEOUT_PLAN) == plan_hash(POST_CLOSEOUT_PLAN)

    # Substantive content is still protected: changing 목표 must change the hash.
    tampered = POST_CLOSEOUT_PLAN.replace(
        "**목표:** Test cryptographic hook", "**목표:** Something else entirely"
    )
    for plan_hash in (ra.plan_hash, ca.plan_hash):
        assert plan_hash(POST_CLOSEOUT_PLAN) != plan_hash(tampered)


def test_reviewed_state_transition_keeps_artifact_valid(tmp_path):
    import sys
    scripts_dir = Path(".agents/skills/harness/writing-plans/scripts").resolve()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import review_artifacts as review
    plan = tmp_path / "plan.md"
    plan.write_text(PRE_CLOSEOUT_PLAN.replace("> reviewed: true", "> reviewed: false"), encoding="utf-8")
    for role, reviewer_id, result in (("plan-reviewer", "r1", "PASS"), ("principle-auditor", "r2", "PASS/CLEAN")):
        review.record_review(tmp_path, "plan.md", role, result, reviewer_id, "test", "ok", None)
    plan.write_text(plan.read_text(encoding="utf-8").replace("> reviewed: false", "> reviewed: true"), encoding="utf-8")
    assert review.check_plan(tmp_path, "plan.md").valid


def test_usability_metadata_forms_are_consistent(tmp_path):
    import sys
    scripts_dir = Path(".agents/skills/harness/writing-plans/scripts").resolve()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import review_artifacts as review
    assert review.required_reviewers_for_text("> **usability_review_required:** true<br>\n")[-1] == "usability-reviewer"
    assert review.required_reviewers_for_text("> usability_review_required: true<br>\n")[-1] == "usability-reviewer"


def test_check_plan_accepts_unresolved_relative_root(tmp_path, monkeypatch):
    """Regression test: Gate 2 review-gate hooks receive `cwd` as a possibly
    relative, unresolved path (e.g. '.', matching a Stop-hook payload with no
    explicit cwd). check_plan() must not crash comparing an absolute plan_file
    against an unresolved relative root."""
    import sys

    scripts_dir = Path(".agents/skills/harness/writing-plans/scripts").resolve()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from review_artifacts import check_plan

    plan_dir = tmp_path / ".agentos" / "project" / "exec-plans" / "active"
    plan_dir.mkdir(parents=True)
    (plan_dir / "2026-07-31-test-hook.md").write_text(PRE_CLOSEOUT_PLAN, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = check_plan(Path("."), ".agentos/project/exec-plans/active/2026-07-31-test-hook.md")
    assert result.plan_path == ".agentos/project/exec-plans/active/2026-07-31-test-hook.md"
