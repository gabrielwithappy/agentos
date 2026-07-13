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
    active_dir = ROOT / "docs/exec-plans/active"
    plans = sorted(active_dir.glob("*.ko.md"))
    if not plans:
        return

    for plan in plans:
        text = plan.read_text(encoding="utf-8")
        assert ("## 사용자 결과 요약" in text) or ("## User Result Brief" in text), plan
        assert ("## 사용자 진행 계획" in text) or ("## User Progress Plan" in text), plan
        assert ("사용자가 무엇을 얻게 되는가?" in text) or ("What will the user get?" in text), plan
        assert ("사용자에게 보이는 결과" in text) or ("User-visible result" in text), plan
