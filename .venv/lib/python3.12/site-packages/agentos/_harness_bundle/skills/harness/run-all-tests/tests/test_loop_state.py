# tests/test_loop_state.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute() / "core-engine"))
from loop_state import LoopState


def test_roundtrip_all_fields(tmp_path):
    """sh read_frontmatter_field와 동일하게 동작하는지 검증"""
    state = LoopState(
        active=True, execution_locked=True, iteration=5, max_iterations=20,
        completion_promise="DONE", cli="gemini",
        loop_id="loop-20260410-abc123",
        last_checkpoint_at='"2026-04-09T00:00:00Z"',
        last_event="checkpoint",
        current_phase="Phase 2-1 완료",
        current_task="reconcile contract",
        current_step="Phase 2-1 완료",
        plan_path=".agentos/project/exec-plans/demo.md",
        prompt_summary="summary",
        result_summary="final answer summary",
        outcome_code="blocked",
        failure_class="escalation_pending",
        status_hint="operator response required",
        blocked_reason="tmux access denied",
        stop_reason="blocked:tmux",
        pending_escalation_id="esc-001",
        pending_escalation_summary="need direction",
        pending_override_response="switch direction",
        prompt="hello world"
    )
    f = tmp_path / "state.md"
    state.to_file(f)
    loaded = LoopState.from_file(f)
    assert loaded.iteration == 5
    assert loaded.cli == "gemini"
    assert loaded.completion_promise == "DONE"
    assert loaded.loop_id == "loop-20260410-abc123"
    assert loaded.prompt == "hello world"
    assert loaded.active is True
    assert loaded.execution_locked is True
    assert loaded.last_checkpoint_at == "2026-04-09T00:00:00Z"
    assert loaded.last_event == "checkpoint"
    assert loaded.current_phase == "Phase 2-1 완료"
    assert loaded.current_task == "reconcile contract"
    assert loaded.current_step == "Phase 2-1 완료"
    assert loaded.plan_path == ".agentos/project/exec-plans/demo.md"
    assert loaded.prompt_summary == "summary"
    assert loaded.result_summary == "final answer summary"
    assert loaded.outcome_code == "blocked"
    assert loaded.failure_class == "escalation_pending"
    assert loaded.status_hint == "operator response required"
    assert loaded.blocked_reason == "tmux access denied"
    assert loaded.stop_reason == "blocked:tmux"
    assert loaded.pending_escalation_id == "esc-001"
    assert loaded.pending_escalation_summary == "need direction"
    assert loaded.pending_override_response == "switch direction"

def test_roundtrip_inactive(tmp_path):
    state = LoopState(active=False, iteration=3)
    f = tmp_path / "state.md"
    state.to_file(f)
    loaded = LoopState.from_file(f)
    assert loaded.active is False

def test_bump_iteration(tmp_path):
    state = LoopState(iteration=1)
    state.bump_iteration()
    assert state.iteration == 2
    assert state.last_run != "null"

def test_roundtrip_blank_observability_fields(tmp_path):
    state = LoopState()
    f = tmp_path / "state.md"
    state.to_file(f)
    loaded = LoopState.from_file(f)
    assert loaded.last_event == ""
    assert loaded.current_phase == ""
    assert loaded.current_task == ""
    assert loaded.current_step == ""
    assert loaded.plan_path == ""
    assert loaded.prompt_summary == ""
    assert loaded.result_summary == ""
    assert loaded.blocked_reason == ""
    assert loaded.stop_reason == ""
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    assert loaded.pending_override_response == ""

def test_diagnostic_fields_round_trip(tmp_path):
    state = LoopState(
        outcome_code="completed",
        failure_class="none",
        status_hint="completion promise accepted with required evidence",
    )
    f = tmp_path / "state.md"
    state.to_file(f)
    text = f.read_text(encoding="utf-8")
    assert "outcome_code: |" in text
    assert "failure_class: |" in text
    assert "status_hint: |" in text
    loaded = LoopState.from_file(f)
    assert loaded.outcome_code == "completed"
    assert loaded.failure_class == "none"
    assert loaded.status_hint == "completion promise accepted with required evidence"

def test_preserves_unknown_empty_diagnostics(tmp_path):
    state = LoopState()
    f = tmp_path / "state.md"
    state.to_file(f)
    loaded = LoopState.from_file(f)
    assert loaded.outcome_code == ""
    assert loaded.failure_class == ""
    assert loaded.status_hint == ""

def test_multiline_block_roundtrip_and_format(tmp_path):
    state = LoopState(
        current_task="Runtime verification\nbounded summary",
        result_summary="line one\nline two",
        pending_escalation_summary="need direction\nwith context",
        prompt="body line 1\nbody line 2",
    )
    f = tmp_path / "state.md"
    state.to_file(f)
    text = f.read_text(encoding="utf-8")
    assert "current_task: |" in text
    assert "result_summary: |" in text
    assert "pending_escalation_summary: |" in text
    loaded = LoopState.from_file(f)
    assert loaded.current_task == "Runtime verification\nbounded summary"
    assert loaded.result_summary == "line one\nline two"
    assert loaded.pending_escalation_summary == "need direction\nwith context"
    assert loaded.prompt == "body line 1\nbody line 2"

def test_deactivate_keeps_file(tmp_path):
    state = LoopState(iteration=1)
    f = tmp_path / "state.md"
    state.to_file(f)
    state.deactivate(f)
    assert f.exists()
    loaded = LoopState.from_file(f)
    assert loaded.active is False

def test_delete_removes_file(tmp_path):
    f = tmp_path / "state.md"
    f.write_text("test")
    LoopState.delete(f)
    assert not f.exists()

def test_delete_missing_ok(tmp_path):
    f = tmp_path / "nonexistent.md"
    LoopState.delete(f)  # 예외 없어야 함
