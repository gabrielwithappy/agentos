from __future__ import annotations

from agentos.terminal.events import CLI_EVENT_SCHEMA_VERSION, CliEvent, wrap_provider_event


def test_parent_turn_id_defaults_to_none_for_legacy_events():
    event = CliEvent(
        type="input_received",
        session_id="s1",
        turn_id="t1",
        provider="mock",
        mode="tui",
    )
    assert event.parent_turn_id is None
    assert event.to_dict()["parent_turn_id"] is None

    # Session lines written before this field existed have no key at all;
    # consumers must read via .get() and treat a missing key the same as None.
    legacy_line = {"type": "input_received", "session_id": "s1", "turn_id": "t1"}
    assert legacy_line.get("parent_turn_id") is None


def test_parent_turn_id_set_to_previous_turn_id():
    first = wrap_provider_event(
        {"type": "message_delta"},
        session_id="s1",
        turn_id="t1",
        provider="mock",
        mode="tui",
    )
    assert first["parent_turn_id"] is None

    second = wrap_provider_event(
        {"type": "message_delta"},
        session_id="s1",
        turn_id="t2",
        provider="mock",
        mode="tui",
        parent_turn_id="t1",
    )
    assert second["parent_turn_id"] == "t1"


def test_parent_turn_id_passed_through_wrap_provider_event():
    result = wrap_provider_event(
        {"type": "tool_call", "metadata": {"name": "x"}},
        session_id="s1",
        turn_id="t2",
        provider="mock",
        mode="tui",
        parent_turn_id="t1",
    )
    assert result["parent_turn_id"] == "t1"
    assert result["turn_id"] == "t2"
    assert result["schema_version"] == CLI_EVENT_SCHEMA_VERSION


def test_branch_id_defaults_to_none_for_legacy_events():
    event = CliEvent(
        type="input_received",
        session_id="s1",
        turn_id="t1",
        provider="mock",
        mode="tui",
    )
    assert event.branch_id is None
    assert event.to_dict()["branch_id"] is None

    # Session lines written before this field existed have no key at all;
    # consumers must read via .get() and treat a missing key the same as None.
    legacy_line = {"type": "input_received", "session_id": "s1", "turn_id": "t1"}
    assert legacy_line.get("branch_id") is None


def test_branch_id_passed_through_wrap_provider_event():
    result = wrap_provider_event(
        {"type": "message_delta"},
        session_id="s1",
        turn_id="t1",
        provider="mock",
        mode="tui",
        branch_id="main",
    )
    assert result["branch_id"] == "main"
