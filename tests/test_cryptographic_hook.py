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
