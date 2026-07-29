from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from agentos.llm.transports.anthropic_messages import (
    ClaudeMessagesTransport,
    _BlockState,
    _build_request_body,
    _retry_after_seconds,
    _tools_to_claude_schema,
    map_claude_frame,
)
from agentos.llm.transports.base import TransportRequest, build_claude_transport_request
from agentos.llm.types import InvocationMessage, InvocationRequest

SENTINEL = os.environ.get("AGENTOS_TEST_SECRET", "sk-ant-oat-test-secret-value")


# --- tool schema translation ---


def test_tools_to_claude_schema_renames_parameters_to_input_schema():
    tools = [
        {"name": "read", "description": "Read a file.", "parameters": {"type": "object", "properties": {"path": {}}}},
        {"name": "bash", "description": "Run a command.", "parameters": {"type": "object", "properties": {"command": {}}}},
    ]
    converted = _tools_to_claude_schema(tools)
    assert converted[0]["name"] == "Read"
    assert converted[0]["input_schema"] == {"type": "object", "properties": {"path": {}}}
    assert "parameters" not in converted[0]
    assert converted[1]["name"] == "Bash"


def test_tools_to_claude_schema_covers_all_seven_agentos_tools():
    from agentos.llm.tools.registry import ALL_TOOL_NAMES, get_tool_schemas

    schemas = get_tool_schemas(list(ALL_TOOL_NAMES))
    converted = _tools_to_claude_schema(schemas)
    assert len(converted) == 7
    for tool in converted:
        assert "input_schema" in tool
        assert "parameters" not in tool


# --- request body ---


def test_build_request_body_includes_model_messages_and_stream():
    request = TransportRequest(model="claude-sonnet-5", messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}])
    body = _build_request_body(request)
    assert body["model"] == "claude-sonnet-5"
    assert body["stream"] is True
    assert body["messages"][0]["role"] == "user"


def test_build_request_body_maps_instructions_to_system_param():
    request = TransportRequest(model="claude-sonnet-5", messages=[], instructions="You are helpful.")
    body = _build_request_body(request)
    assert body["system"] == "You are helpful."


def test_oauth_request_body_puts_claude_code_identity_first_and_preserves_instructions():
    request = TransportRequest(model="claude-sonnet-5", messages=[], instructions="Keep this instruction.")
    body = _build_request_body(request, oauth=True)
    assert body["system"] == [
        {"type": "text", "text": "You are Claude Code, Anthropic's official CLI for Claude."},
        {"type": "text", "text": "Keep this instruction."},
    ]


def test_build_request_body_omits_system_when_absent():
    request = TransportRequest(model="claude-sonnet-5", messages=[])
    body = _build_request_body(request)
    assert "system" not in body


def test_build_request_body_includes_tools_in_claude_schema():
    request = TransportRequest(
        model="claude-sonnet-5",
        messages=[],
        tools=[{"name": "read", "description": "Read.", "parameters": {"type": "object"}}],
    )
    body = _build_request_body(request)
    assert body["tools"][0]["input_schema"] == {"type": "object"}


# --- build_claude_transport_request: system separation, tool round-trip ---


def test_build_claude_transport_request_separates_system_messages_into_instructions():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="system", text="You are AgentOS."),
            InvocationMessage(role="user", text="hello"),
        ]
    )
    request = build_claude_transport_request(model="claude-sonnet-5", invocation_request=invocation_request)
    assert request.instructions == "You are AgentOS."
    assert request.messages == [{"role": "user", "content": [{"type": "text", "text": "hello"}]}]


def test_build_claude_transport_request_ignores_continuation():
    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="hi")],
        continuation="some-opaque-handle",
    )
    request = build_claude_transport_request(model="claude-sonnet-5", invocation_request=invocation_request)
    assert request.previous_response_id is None


def test_build_claude_transport_request_converts_correlated_tool_message_to_tool_use_and_result_blocks():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="list files"),
            InvocationMessage(
                role="tool",
                text="a.txt\nb.txt",
                metadata={"call_id": "call-1", "name": "list", "arguments": '{"path": "."}'},
            ),
        ]
    )
    request = build_claude_transport_request(model="claude-sonnet-5", invocation_request=invocation_request)
    assert request.messages[0]["role"] == "user"
    assert request.messages[1]["role"] == "assistant"
    assert request.messages[1]["content"][0]["type"] == "tool_use"
    assert request.messages[1]["content"][0]["id"] == "call-1"
    assert request.messages[1]["content"][0]["input"] == {"path": "."}
    assert request.messages[2]["role"] == "user"
    assert request.messages[2]["content"][0]["type"] == "tool_result"
    assert request.messages[2]["content"][0]["tool_use_id"] == "call-1"
    assert request.messages[2]["content"][0]["content"] == "a.txt\nb.txt"


def test_build_claude_transport_request_omits_uncorrelated_legacy_tool_message():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="hi"),
            InvocationMessage(role="tool", text="legacy output with no call metadata"),
        ]
    )
    request = build_claude_transport_request(model="claude-sonnet-5", invocation_request=invocation_request)
    assert len(request.messages) == 1
    assert request.messages[0]["role"] == "user"


def test_build_claude_transport_request_forwards_tools():
    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="hi")],
        tools=[{"name": "read", "description": "Read.", "parameters": {"type": "object"}}],
    )
    request = build_claude_transport_request(model="claude-sonnet-5", invocation_request=invocation_request)
    assert request.tools == [{"name": "read", "description": "Read.", "parameters": {"type": "object"}}]


# --- SSE frame mapping: single events ---


def test_message_start_maps_to_start_event():
    event = map_claude_frame({"type": "message_start"}, _BlockState())
    assert event.type == "start"


def test_content_block_start_text_yields_no_event():
    state = _BlockState()
    event = map_claude_frame({"type": "content_block_start", "index": 0, "content_block": {"type": "text"}}, state)
    assert event is None
    assert state.block_type[0] == "text"


def test_content_block_start_tool_use_registers_name_and_id():
    state = _BlockState()
    event = map_claude_frame(
        {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "call-1", "name": "read"}},
        state,
    )
    assert event is None
    assert state.tool_id[1] == "call-1"
    assert state.tool_name[1] == "read"


def test_content_block_start_restores_claude_code_tool_name_to_agentos_registry_name():
    state = _BlockState()
    map_claude_frame(
        {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "call-1", "name": "Bash"}},
        state,
    )
    assert state.tool_name[1] == "bash"


def test_text_delta_maps_to_message_delta_event():
    state = _BlockState()
    state.block_type[0] = "text"
    event = map_claude_frame({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "hi"}}, state)
    assert event.type == "message_delta"
    assert event.text == "hi"


def test_input_json_delta_buffers_without_emitting_event():
    state = _BlockState()
    state.block_type[1] = "tool_use"
    state.tool_json_buffer[1] = ""
    event = map_claude_frame(
        {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": '{"path"'}}, state
    )
    assert event is None
    event2 = map_claude_frame(
        {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": ': "."}'}}, state
    )
    assert event2 is None
    assert state.tool_json_buffer[1] == '{"path": "."}'


def test_content_block_stop_for_tool_use_emits_tool_call_with_parsed_arguments():
    state = _BlockState()
    state.block_type[1] = "tool_use"
    state.tool_id[1] = "call-1"
    state.tool_name[1] = "list"
    state.tool_json_buffer[1] = '{"path": "."}'
    event = map_claude_frame({"type": "content_block_stop", "index": 1}, state)
    assert event.type == "tool_call"
    assert event.metadata == {"name": "list", "arguments": {"path": "."}, "call_id": "call-1"}


def test_content_block_stop_for_tool_use_with_malformed_json_falls_back_to_empty_dict():
    state = _BlockState()
    state.block_type[1] = "tool_use"
    state.tool_id[1] = "call-1"
    state.tool_name[1] = "list"
    state.tool_json_buffer[1] = "not json"
    event = map_claude_frame({"type": "content_block_stop", "index": 1}, state)
    assert event.metadata["arguments"] == {}


def test_content_block_stop_for_text_block_yields_no_event():
    state = _BlockState()
    state.block_type[0] = "text"
    event = map_claude_frame({"type": "content_block_stop", "index": 0}, state)
    assert event is None


def test_message_delta_with_usage_buffers_without_emitting_event():
    state = _BlockState()
    event = map_claude_frame({"type": "message_delta", "usage": {"input_tokens": 10, "output_tokens": 5}}, state)
    assert event is None
    assert state.usage == {"input_tokens": 10, "output_tokens": 5}


def test_message_stop_maps_to_done_event_with_buffered_usage():
    state = _BlockState()
    state.usage = {"input_tokens": 10, "output_tokens": 5}
    event = map_claude_frame({"type": "message_stop"}, state)
    assert event.type == "done"
    assert event.usage == {"input_tokens": 10, "output_tokens": 5}


def test_unknown_frame_type_is_dropped_without_raising():
    event = map_claude_frame({"type": "some_unknown_future_event"}, _BlockState())
    assert event is None


# --- error frame classification ---


def test_error_frame_with_authentication_error_type_classifies_as_token_expired():
    event = map_claude_frame({"type": "error", "error": {"type": "authentication_error", "message": "expired"}}, _BlockState())
    assert event.type == "error"
    assert event.error["code"] == "token_expired"


def test_error_frame_with_other_error_type_classifies_as_integration_blocked():
    event = map_claude_frame({"type": "error", "error": {"type": "permission_error", "message": "blocked"}}, _BlockState())
    assert event.error["code"] == "claude_integration_blocked"


def test_error_frame_message_is_redacted(monkeypatch):
    monkeypatch.setattr(
        "agentos.llm.transports.anthropic_messages.redact_text", lambda text: text.replace(SENTINEL, "[REDACTED]")
    )
    event = map_claude_frame({"type": "error", "error": {"type": "authentication_error", "message": f"token {SENTINEL} invalid"}}, _BlockState())
    assert SENTINEL not in event.error["message"]


# --- multi-block interleaved sequence (text + tool_use) ---


def test_interleaved_text_and_tool_use_blocks_yield_correct_ordered_events():
    frames = [
        {"type": "message_start"},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text"}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Let me check "}},
        {"type": "content_block_stop", "index": 0},
        {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "call-1", "name": "list"}},
        {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": '{"path": "."}'}},
        {"type": "content_block_stop", "index": 1},
        {"type": "message_delta", "usage": {"input_tokens": 3, "output_tokens": 7}},
        {"type": "message_stop"},
    ]
    state = _BlockState()
    events = [event for frame in frames if (event := map_claude_frame(frame, state)) is not None]
    types = [event.type for event in events]
    assert types == ["start", "message_delta", "tool_call", "done"]
    assert events[1].text == "Let me check "
    assert events[2].metadata == {"name": "list", "arguments": {"path": "."}, "call_id": "call-1"}
    assert events[3].usage == {"input_tokens": 3, "output_tokens": 7}


# --- ClaudeMessagesTransport.stream() end-to-end with a fake SSE client ---


class FakeSseClient:
    def __init__(self, sse_text: str):
        self.sse_text = sse_text
        self.calls: list[tuple[str, dict, dict]] = []

    def stream_lines(self, url, *, headers, body):
        self.calls.append((url, headers, body))
        for line in self.sse_text.splitlines():
            yield line


def _sse_event(payload: dict) -> str:
    import json as _json

    return f"data: {_json.dumps(payload)}\n"


def test_stream_end_to_end_yields_events_and_sends_oauth_headers():
    sse_text = "".join(
        [
            _sse_event({"type": "message_start"}) + "\n",
            _sse_event({"type": "content_block_start", "index": 0, "content_block": {"type": "text"}}) + "\n",
            _sse_event({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "hi"}}) + "\n",
            _sse_event({"type": "content_block_stop", "index": 0}) + "\n",
            _sse_event({"type": "message_delta", "usage": {"input_tokens": 1, "output_tokens": 1}}) + "\n",
            _sse_event({"type": "message_stop"}) + "\n",
        ]
    )
    fake_client = FakeSseClient(sse_text)
    transport = ClaudeMessagesTransport(access_token_provider=lambda: "sk-ant-oat-fake-token", sse_client=fake_client)
    request = TransportRequest(model="claude-sonnet-5", messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}])

    events = list(transport.stream(request))

    assert [event.type for event in events] == ["start", "message_delta", "done"]
    assert fake_client.calls, "sse client was not invoked"
    _, headers, _ = fake_client.calls[0]
    assert headers["authorization"] == "Bearer sk-ant-oat-fake-token"
    assert headers["anthropic-beta"] == "claude-code-20250219,oauth-2025-04-20"
    assert headers["anthropic-dangerous-direct-browser-access"] == "true"
    assert headers["user-agent"] == "claude-cli/2.1.75"
    assert headers["x-app"] == "cli"


def test_retry_after_seconds_accepts_delta_and_http_date_but_rejects_untrusted_values():
    now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
    assert _retry_after_seconds("30", now=now) == 30
    assert _retry_after_seconds("Tue, 29 Jul 2026 12:00:45 GMT", now=now) == 45
    assert _retry_after_seconds("token=" + SENTINEL, now=now) is None
    assert _retry_after_seconds("999999", now=now) is None
