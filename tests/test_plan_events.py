from pathlib import Path
from agentos.observability.plan_events import emit_plan_writing_started, emit_plan_status_changed

def test_emit_plan_writing_started_payload_fields():
    payload = emit_plan_writing_started("user request", "test_agent", "session123", Path("/path/to/plan.md"), "Plan Title")
    assert payload["event"] == "PLAN_WRITING_STARTED"
    assert payload["user_request"] == "user request"
    assert payload["agent"] == "test_agent"
    assert payload["session"] == "session123"
    assert payload["plan_path"] == "/path/to/plan.md"
    assert payload["plan_title"] == "Plan Title"

def test_emit_plan_writing_started_empty_plan_info():
    payload = emit_plan_writing_started("user request", "test_agent", "session123")
    assert payload["plan_path"] == ""
    assert payload["plan_title"] == ""

def test_emit_plan_status_changed_payload_fields(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("# My Title\n\n> **상태:** 리뷰 대기\n> reviewed: true\n", encoding="utf-8")
    
    payload = emit_plan_status_changed(plan_file)
    assert payload["event"] == "PLAN_STATUS_CHANGED"
    assert payload["title"] == "My Title"
    assert payload["status_text"] == "리뷰 대기"
    assert payload["reviewed"] == "true"
    assert payload["board_status"] == "Ready"
    assert payload["plan_path"] == str(plan_file)

def test_emit_plan_writing_started_no_adapter():
    from agentos.observability.notifier import notifier
    payload = emit_plan_writing_started("req", "agy", "ses")
    notifier.clear_adapters()
    outcomes = notifier.notify_and_wait(payload)
    assert len(outcomes) == 0
