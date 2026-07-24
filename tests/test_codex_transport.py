from __future__ import annotations

import os

import pytest

from agentos.llm.transports.base import ProviderEvent, TransportError, TransportRequest
from agentos.llm.transports.openai_codex_responses import (
    CodexNativeTransport,
    map_codex_frame,
    resolve_responses_url,
    resolve_websocket_url,
)

SENTINEL = "SENTINEL_SECRET"


# --- request_body / session_id / protocol ---


def test_request_body_includes_model_and_messages():
    request = TransportRequest(model="gpt-5-codex", messages=[{"role": "user", "content": "hi"}])
    body = request.to_request_body()
    assert body["model"] == "gpt-5-codex"
    assert body["input"] == [{"role": "user", "content": "hi"}]
    assert body["stream"] is True


def test_request_body_omits_previous_response_id_when_absent():
    request = TransportRequest(model="gpt-5-codex", messages=[])
    body = request.to_request_body()
    assert "previous_response_id" not in body


def test_request_body_includes_previous_response_id_when_present():
    request = TransportRequest(model="gpt-5-codex", messages=[], previous_response_id="resp_123")
    body = request.to_request_body()
    assert body["previous_response_id"] == "resp_123"


def test_session_id_is_generated_when_not_provided():
    a = TransportRequest(model="gpt-5-codex", messages=[])
    b = TransportRequest(model="gpt-5-codex", messages=[])
    assert a.session_id != b.session_id


def test_session_id_is_stable_when_explicitly_provided():
    request = TransportRequest(model="gpt-5-codex", messages=[], session_id="fixed-session")
    assert request.session_id == "fixed-session"


def test_protocol_resolves_responses_url_from_default_base():
    url = resolve_responses_url()
    assert url.endswith("/codex/responses")


def test_protocol_resolves_websocket_url_scheme_from_https():
    ws_url = resolve_websocket_url("https://example.com/backend-api")
    assert ws_url.startswith("wss://")


def test_protocol_maps_response_created_frame_to_start_event():
    event = map_codex_frame({"type": "response.created", "response": {"id": "resp_1"}})
    assert event is not None
    assert event.type == "start"
    assert event.response_id == "resp_1"


# --- websocket_stream / sse_fallback / transport_error / timeout ---


class FakeSseClient:
    def __init__(self, frames: list[dict]):
        self.frames = frames
        self.calls: list[tuple[str, dict, dict]] = []

    def stream_lines(self, url: str, *, headers: dict, body: dict):
        self.calls.append((url, headers, body))
        for frame in self.frames:
            import json

            yield f"data: {json.dumps(frame)}"
            yield ""


class FailingSseClient:
    def stream_lines(self, url: str, *, headers: dict, body: dict):
        raise TransportError("sse_connection_failed", "Streaming connection failed.", retryable=True)
        yield  # pragma: no cover


def _token_provider():
    return "fake-access-token"


def test_sse_fallback_is_used_when_no_websocket_client_available():
    frames = [
        {"type": "response.created", "response": {"id": "resp_1"}},
        {"type": "response.output_text.delta", "delta": "hello", "response": {"id": "resp_1"}},
        {"type": "response.completed", "response": {"id": "resp_1", "usage": {"input_tokens": 1, "output_tokens": 2}}},
    ]
    sse_client = FakeSseClient(frames)
    transport = CodexNativeTransport(access_token_provider=_token_provider, sse_client=sse_client, force_sse=True)
    request = TransportRequest(model="gpt-5-codex", messages=[{"role": "user", "content": "hi"}])
    events = list(transport.stream(request))

    assert [e.type for e in events] == ["start", "message_delta", "done"]
    assert events[1].text == "hello"
    assert sse_client.calls[0][1]["Authorization"] == "Bearer fake-access-token"


def test_websocket_stream_used_when_client_is_injected():
    import json

    class FakeWebSocketClient:
        def send_and_stream(self, url, *, headers, body):
            yield json.dumps({"type": "response.created", "response": {"id": "resp_ws"}})
            yield json.dumps({"type": "response.completed", "response": {"id": "resp_ws"}})

    transport = CodexNativeTransport(
        access_token_provider=_token_provider,
        websocket_client=FakeWebSocketClient(),
    )
    request = TransportRequest(model="gpt-5-codex", messages=[])
    events = list(transport.stream(request))
    assert [e.type for e in events] == ["start", "done"]


def test_transport_error_is_raised_on_sse_connection_failure():
    transport = CodexNativeTransport(
        access_token_provider=_token_provider, sse_client=FailingSseClient(), force_sse=True
    )
    request = TransportRequest(model="gpt-5-codex", messages=[])
    with pytest.raises(TransportError):
        list(transport.stream(request))


def test_transport_error_is_retryable_for_connection_failure():
    transport = CodexNativeTransport(
        access_token_provider=_token_provider, sse_client=FailingSseClient(), force_sse=True
    )
    request = TransportRequest(model="gpt-5-codex", messages=[])
    try:
        list(transport.stream(request))
    except TransportError as exc:
        assert exc.retryable is True


def test_timeout_like_failure_maps_to_response_failed_frame():
    event = map_codex_frame({"type": "response.failed", "error": {"code": "timeout", "message": "Request timed out"}})
    assert event is not None
    assert event.type == "error"
    assert event.error["code"] == "timeout"


# --- message_delta / reasoning / tool_call / tool_result / done / usage / secret / stderr ---


def test_message_delta_frame_is_redacted(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    event = map_codex_frame(
        {"type": "response.output_text.delta", "delta": f"token is {SENTINEL}", "response": {"id": "r1"}}
    )
    assert event is not None
    assert SENTINEL not in event.text


def test_reasoning_frame_maps_to_reasoning_event():
    event = map_codex_frame(
        {"type": "response.reasoning_summary_text.delta", "delta": "thinking...", "response": {"id": "r1"}}
    )
    assert event is not None
    assert event.type == "reasoning"
    assert event.text == "thinking..."


def test_tool_call_frame_maps_to_tool_call_event():
    event = map_codex_frame(
        {
            "type": "response.output_item.added",
            "item": {"type": "function_call", "name": "search", "arguments": "{}"},
            "response": {"id": "r1"},
        }
    )
    assert event is not None
    assert event.type == "tool_call"
    assert event.metadata["name"] == "search"


def test_tool_result_frame_maps_to_tool_result_event():
    event = map_codex_frame(
        {
            "type": "response.output_item.done",
            "item": {"type": "function_call_output", "output": "42"},
            "response": {"id": "r1"},
        }
    )
    assert event is not None
    assert event.type == "tool_result"
    assert event.metadata["summary"] == "42"


def test_done_frame_includes_usage():
    event = map_codex_frame(
        {
            "type": "response.completed",
            "response": {"id": "r1", "usage": {"input_tokens": 5, "output_tokens": 7}},
        }
    )
    assert event is not None
    assert event.type == "done"
    assert event.usage == {"input_tokens": 5, "output_tokens": 7}


def test_error_frame_message_is_redacted(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    event = map_codex_frame(
        {"type": "error", "error": {"code": "internal", "message": f"leaked {SENTINEL} in stderr"}}
    )
    assert event is not None
    assert SENTINEL not in event.error["message"]


def test_unknown_frame_type_is_dropped_without_raising():
    event = map_codex_frame({"type": "response.some_future_event", "response": {"id": "r1"}})
    assert event is None


def test_sse_stream_never_exposes_raw_sentinel_in_any_event_field(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    frames = [
        {"type": "response.created", "response": {"id": "resp_1"}},
        {
            "type": "response.output_text.delta",
            "delta": f"secret={SENTINEL}",
            "response": {"id": "resp_1"},
        },
        {"type": "error", "error": {"code": "boom", "message": f"stderr dump: {SENTINEL}"}},
    ]
    sse_client = FakeSseClient(frames)
    transport = CodexNativeTransport(access_token_provider=_token_provider, sse_client=sse_client, force_sse=True)
    request = TransportRequest(model="gpt-5-codex", messages=[])
    events = list(transport.stream(request))
    serialized = "".join(str(vars(e)) for e in events)
    assert SENTINEL not in serialized
