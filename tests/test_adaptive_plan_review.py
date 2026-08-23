from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(".agents/skills/harness/writing-plans/scripts").resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from review_artifacts import check_plan, record_review, record_self_check
from review_policy import classify_plan


def _write_plan(root: Path, text: str) -> str:
    path = root / ".agentos/project/exec-plans/active/2026-08-23-example.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path.relative_to(root).as_posix()


SIMPLE_PLAN = """# Docs plan

> reviewed: true

## File Structure
- 수정: `docs/guide.md`
- 수정: `docs/faq.md`
"""


def test_classifier_allows_only_small_non_sensitive_markdown_surface():
    policy = classify_plan(SIMPLE_PLAN)

    assert policy.tier == "simple"
    assert policy.review_required is False
    assert policy.reviewers == ()
    assert policy.model_class == "none"


def test_classifier_escalates_protected_user_facing_plan_despite_declared_simple_tier():
    policy = classify_plan(
        """review_tier: simple
review_required: false
usability_review_required: true

## File Structure
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`
- 수정: `docs/cli-reference.md`
CLI setup flow changes.
"""
    )

    assert policy.tier == "high-risk"
    assert policy.review_required is True
    assert policy.reviewers == ("plan-reviewer", "principle-auditor", "usability-reviewer")
    assert policy.model_class == "capable"


def test_classifier_uses_single_economy_reviewer_for_standard_code_change():
    policy = classify_plan("## File Structure\n- 수정: `agentos/runtime.py`\n")

    assert policy.tier == "standard"
    assert policy.reviewers == ("plan-reviewer",)
    assert policy.max_tokens == 3000
    assert policy.max_seconds == 120


def test_simple_plan_requires_self_check_before_execution_gate_is_valid(tmp_path):
    plan_path = _write_plan(tmp_path, SIMPLE_PLAN)

    missing = check_plan(tmp_path, plan_path)
    assert missing.valid is False
    assert missing.missing == ["self-check"]

    record_self_check(tmp_path, plan_path, "docs links checked", "rg -n 'knowledge-curator' docs")
    checked = check_plan(tmp_path, plan_path)

    assert checked.valid is True
    assert checked.policy.tier == "simple"
    assert checked.artifacts["self-check"]["validator"] == "rg -n 'knowledge-curator' docs"


def test_self_check_cannot_bypass_standard_plan(tmp_path):
    plan_path = _write_plan(tmp_path, "## File Structure\n- 수정: `agentos/runtime.py`\n")

    with pytest.raises(ValueError, match="only allowed for simple"):
        record_self_check(tmp_path, plan_path, "checked", "pytest -q")


def test_standard_plan_requires_only_plan_reviewer(tmp_path):
    plan_path = _write_plan(tmp_path, "## File Structure\n- 수정: `agentos/runtime.py`\n")

    record_review(
        tmp_path,
        plan_path,
        "plan-reviewer",
        "PASS",
        "reviewer-1",
        "subagent",
        "scope and verification checked",
        "implementer",
        usage_tokens=1440,
        duration_ms=9000,
    )

    checked = check_plan(tmp_path, plan_path)
    assert checked.valid is True
    assert checked.required_reviewers == ["plan-reviewer"]
    assert checked.artifacts["plan-reviewer"]["usage_tokens"] == 1440
    assert checked.artifacts["plan-reviewer"]["duration_ms"] == 9000
