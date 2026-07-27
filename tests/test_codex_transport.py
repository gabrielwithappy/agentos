from __future__ import annotations

import os

import pytest

from agentos.llm.transports.base import (
    ProviderEvent,
    TransportError,
    TransportRequest,
    build_transport_request,
)
from agentos.llm.transports.openai_codex_responses import (
    CodexNativeTransport,
    map_codex_frame,
    resolve_responses_url,
    resolve_websocket_url,
)
from agentos.conversation.types import ProviderContinuation
from agentos.llm.types import InvocationMessage, InvocationRequest

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


def test_build_transport_request_from_invocation_request_preserves_message_order():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="system", text="be terse"),
            InvocationMessage(role="user", text="turn one"),
            InvocationMessage(role="assistant", text="reply one"),
            InvocationMessage(role="user", text="turn two"),
        ]
    )

    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)

    assert transport_request.instructions == "be terse"
    assert transport_request.messages == [
        {"role": "user", "content": "turn one"},
        {"role": "assistant", "content": "reply one"},
        {"role": "user", "content": "turn two"},
    ]


def test_build_transport_request_sets_previous_response_id_from_continuation():
    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="turn two")],
        continuation="resp_abc123",
    )

    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)

    assert transport_request.previous_response_id == "resp_abc123"


def test_build_transport_request_uses_message_replay_when_continuation_is_none():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="turn one"),
            InvocationMessage(role="assistant", text="reply one"),
            InvocationMessage(role="user", text="turn two"),
        ],
        continuation=None,
    )

    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)

    assert transport_request.previous_response_id is None
    assert len(transport_request.messages) == 3


# --- tools ---


def test_request_body_omits_tools_when_absent():
    request = TransportRequest(model="gpt-5-codex", messages=[])
    body = request.to_request_body()
    assert "tools" not in body


def test_request_body_includes_tools_when_present():
    request = TransportRequest(
        model="gpt-5-codex",
        messages=[],
        tools=[{"name": "read", "description": "Read a file", "parameters": {"type": "object", "properties": {}}}],
    )
    body = request.to_request_body()
    assert body["tools"] == [
        {
            "type": "function",
            "name": "read",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        }
    ]


def test_build_transport_request_omits_tools_when_invocation_request_has_none():
    invocation_request = InvocationRequest(messages=[InvocationMessage(role="user", text="hi")])
    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)
    assert transport_request.tools is None
    assert "tools" not in transport_request.to_request_body()


def test_build_transport_request_forwards_tools_from_invocation_request():
    tool_spec = {"name": "read", "description": "Read a file", "parameters": {"type": "object", "properties": {}}}
    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="hi")],
        tools=[tool_spec],
    )
    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)
    assert transport_request.tools == [tool_spec]


def test_build_transport_request_replays_correlated_tool_as_call_and_output():
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="list files"),
            InvocationMessage(
                role="tool",
                text="README.md",
                metadata={"call_id": "call_list", "name": "list", "arguments": '{"path":"."}'},
            ),
        ]
    )
    body = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request).to_request_body()
    assert body["input"] == [
        {"role": "user", "content": "list files"},
        {"type": "function_call", "call_id": "call_list", "name": "list", "arguments": '{"path":"."}'},
        {"type": "function_call_output", "call_id": "call_list", "output": "README.md"},
    ]


def test_build_transport_request_omits_uncorrelated_legacy_tool_message():
    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="continue"), InvocationMessage(role="tool", text="old result")]
    )
    body = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request).to_request_body()
    assert body["input"] == [{"role": "user", "content": "continue"}]


# --- continuation_expired / branch_change / provider_switch / restart / resume / transport_epoch / replay ---


def test_continuation_expired_or_epoch_mismatch_forces_bounded_replay_on_restart_or_resume():
    continuation = ProviderContinuation(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="main",
        transport_session_epoch="epoch-before-restart",
        handle="resp_prev",
    )

    # A new process incarnation (restart/resume) always mints a fresh
    # transport-session epoch, so a persisted continuation from a previous
    # epoch never matches and must never be reused.
    valid_after_resume = continuation.matches(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="main",
        transport_session_epoch="epoch-after-restart",
    )
    assert valid_after_resume is False

    invocation_request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="turn two")],
        continuation=continuation.handle if valid_after_resume else None,
    )
    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)

    assert transport_request.previous_response_id is None
    assert len(transport_request.messages) == 1


def test_build_transport_request_omits_continuation_when_branch_change_invalidates_scope():
    continuation = ProviderContinuation(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="branch-a",
        transport_session_epoch="epoch-1",
        handle="resp_a",
    )

    valid_for_branch_b = continuation.matches(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="branch-b",
        transport_session_epoch="epoch-1",
    )

    assert valid_for_branch_b is False


def test_build_transport_request_omits_continuation_when_provider_switch_invalidates_scope():
    continuation = ProviderContinuation(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="main",
        transport_session_epoch="epoch-1",
        handle="resp_a",
    )

    valid_after_switching_to_codex_cli = continuation.matches(
        provider="codex-cli",
        model="gpt-5-codex",
        account="default",
        branch_id="main",
        transport_session_epoch="epoch-1",
    )

    assert valid_after_switching_to_codex_cli is False


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


def test_output_item_added_for_function_call_does_not_emit_tool_call_yet():
    # The Codex ChatGPT-account backend leaves `arguments` empty/in-progress
    # at this point in the stream — the complete item (name + arguments)
    # only arrives later on `response.output_item.done`.
    event = map_codex_frame(
        {
            "type": "response.output_item.added",
            "item": {
                "id": "fc_1",
                "type": "function_call",
                "status": "in_progress",
                "arguments": "",
                "call_id": "call_1",
                "name": "search",
            },
            "response": {"id": "r1"},
        }
    )
    assert event is None


def test_function_call_arguments_delta_is_ignored():
    event = map_codex_frame(
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": "{\"query\":",
            "output_index": 1,
        }
    )
    assert event is None


def test_function_call_arguments_done_is_ignored():
    # Unlike the documented OpenAI platform Responses API, the Codex
    # ChatGPT-account backend's `.done` frame carries only `arguments` and
    # `item_id` — no `name` — so it cannot be used to build a `tool_call`
    # event on its own. `response.output_item.done` is used instead (see
    # below), since it repeats the complete `arguments` alongside `name`.
    event = map_codex_frame(
        {
            "type": "response.function_call_arguments.done",
            "arguments": '{"query": "hello"}',
            "item_id": "fc_1",
            "output_index": 1,
        }
    )
    assert event is None


def test_output_item_done_for_function_call_maps_to_tool_call_event_with_parsed_arguments():
    event = map_codex_frame(
        {
            "type": "response.output_item.done",
            "item": {
                "id": "fc_1",
                "type": "function_call",
                "status": "completed",
                "arguments": '{"path": "."}',
                "call_id": "call_1",
                "name": "list",
            },
            "output_index": 1,
            "response": {"id": "r1"},
        }
    )
    assert event is not None
    assert event.type == "tool_call"
    assert event.metadata["name"] == "list"
    assert event.metadata["arguments"] == {"path": "."}
    assert event.metadata["call_id"] == "call_1"


def test_output_item_done_for_function_call_with_empty_arguments_yields_empty_dict():
    event = map_codex_frame(
        {
            "type": "response.output_item.done",
            "item": {"type": "function_call", "arguments": "", "call_id": "call_1", "name": "list"},
            "response": {"id": "r1"},
        }
    )
    assert event is not None
    assert event.metadata["arguments"] == {}


def test_output_item_done_for_function_call_with_malformed_json_falls_back_to_empty_dict():
    event = map_codex_frame(
        {
            "type": "response.output_item.done",
            "item": {"type": "function_call", "arguments": "{not valid json", "call_id": "call_1", "name": "list"},
            "response": {"id": "r1"},
        }
    )
    assert event is not None
    assert event.metadata["arguments"] == {}


def test_full_tool_call_stream_sequence_yields_single_tool_call_with_dict_arguments():
    # Reproduces the real Codex ChatGPT-account backend frame order,
    # captured from a live session: output_item.added (empty arguments) ->
    # zero or more argument deltas -> function_call_arguments.done (no
    # `name`, ignored) -> output_item.done (complete item: name +
    # arguments).
    frames = [
        {"type": "response.created", "response": {"id": "r1"}},
        {
            "type": "response.output_item.added",
            "item": {"id": "fc_1", "type": "function_call", "status": "in_progress", "arguments": "", "call_id": "call_1", "name": "list"},
            "output_index": 1,
        },
        {"type": "response.function_call_arguments.delta", "item_id": "fc_1", "delta": "{}", "output_index": 1},
        {
            "type": "response.function_call_arguments.done",
            "arguments": "{}",
            "item_id": "fc_1",
            "output_index": 1,
        },
        {
            "type": "response.output_item.done",
            "item": {"id": "fc_1", "type": "function_call", "status": "completed", "arguments": "{}", "call_id": "call_1", "name": "list"},
            "output_index": 1,
        },
        {"type": "response.completed", "response": {"id": "r1"}},
    ]
    events = [e for e in (map_codex_frame(f) for f in frames) if e is not None]
    tool_call_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_call_events) == 1
    assert tool_call_events[0].metadata["arguments"] == {}
    assert tool_call_events[0].metadata["name"] == "list"


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


# --- request_capture / transport_error / diagnostics via build_transport_request ---


def test_build_transport_request_redacts_secret_from_request_capture(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="system", text=f"instruction leak {SENTINEL}"),
            InvocationMessage(role="user", text=f"token={SENTINEL}"),
        ]
    )

    transport_request = build_transport_request(model="gpt-5-codex", invocation_request=invocation_request)
    captured = str(vars(transport_request))

    assert SENTINEL not in captured
    assert SENTINEL not in transport_request.instructions
    assert SENTINEL not in transport_request.messages[0]["content"]


def test_stream_via_native_provider_transport_error_diagnostics_never_expose_sentinel(monkeypatch, tmp_path):
    from agentos.llm.auth.openai_codex import TokenResult, persist_tokens
    from agentos.llm.auth.store import AuthFileStore
    import agentos.llm.providers.codex_native as codex_native_module

    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    home = tmp_path / "home"
    store = AuthFileStore(home=home)
    persist_tokens(
        TokenResult(id_token="id", access_token="access-token-1", refresh_token="refresh-1", expires_in=3600),
        store=store,
    )

    class FailingTransport:
        def stream(self, request):
            raise TransportError("boom", f"native transport failure: {SENTINEL}", retryable=True)
            yield  # pragma: no cover - makes this a generator function

    provider = codex_native_module.CodexNativeProvider(
        store=store, transport_factory=lambda token, account_id: FailingTransport()
    )
    request = InvocationRequest(
        messages=[InvocationMessage(role="user", text="hello")],
        continuation="resp_prev",
    )

    events = list(provider.stream_context(request))
    serialized = "".join(str(vars(e)) for e in events)

    assert events[-1].type == "error"
    assert SENTINEL not in serialized


def test_stream_context_request_and_events_never_expose_raw_sentinel(monkeypatch, tmp_path):
    from agentos.llm.auth.openai_codex import TokenResult, persist_tokens
    from agentos.llm.auth.store import AuthFileStore
    import agentos.llm.providers.codex_native as codex_native_module

    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    home = tmp_path / "home"
    store = AuthFileStore(home=home)
    persist_tokens(
        TokenResult(id_token="id", access_token="access-token-1", refresh_token="refresh-1", expires_in=3600),
        store=store,
    )

    captured = {}

    class FakeTransport:
        def stream(self, request):
            captured["request"] = request
            yield ProviderEvent(type="start", response_id="resp_1")
            yield ProviderEvent(type="message_delta", text=f"leaked {SENTINEL}", response_id="resp_1")
            yield ProviderEvent(type="done", response_id="resp_1", usage={"input_tokens": 1, "output_tokens": 2})

    provider = codex_native_module.CodexNativeProvider(
        store=store, transport_factory=lambda token, account_id: FakeTransport()
    )
    request = InvocationRequest(
        messages=[InvocationMessage(role="user", text=f"token={SENTINEL}")],
        continuation="resp_prev",
    )

    events = list(provider.stream_context(request))

    assert SENTINEL not in str(vars(captured["request"]))
    assert captured["request"].previous_response_id == "resp_prev"
    assert all(SENTINEL not in str(vars(e)) for e in events)


# ── bugfix regression: device-code fallback failure must not crash login() ──


def test_login_device_code_fallback_failure_returns_sanitized_status_not_exception(tmp_path, monkeypatch):
    """When the browser cannot be launched AND the device-code fallback also
    fails (e.g. no network access to the auth issuer), `login()` must return
    a sanitized failed `ProviderStatus`, never let the device-code
    `AuthError` propagate uncaught — that crashed the Textual worker thread
    in production (`except auth.BrowserLaunchFailedError:` swallowed the
    original browser failure but did not wrap the fallback attempt in its
    own try/except, so a device-code `AuthError` had no handler)."""
    import agentos.llm.auth.openai_codex as auth_module
    import agentos.llm.providers.codex_native as codex_native_module
    from agentos.llm.auth.store import AuthFileStore

    def fake_complete_browser_login(prepared, **kwargs):
        raise auth_module.BrowserLaunchFailedError()

    def fake_request_device_code(*args, **kwargs):
        raise auth_module.AuthError("device_code_request_failed", "Could not start device sign-in.")

    monkeypatch.setattr(auth_module, "complete_browser_login", fake_complete_browser_login)
    monkeypatch.setattr(auth_module, "request_device_code", fake_request_device_code)

    provider = codex_native_module.CodexNativeProvider(store=AuthFileStore(home=tmp_path))

    status = provider.login()

    assert status.authenticated is False
    assert status.status == "failed"
    assert status.recovery


def test_login_updates_device_code_fallback_failure_yields_result_not_exception(tmp_path, monkeypatch):
    import agentos.llm.auth.openai_codex as auth_module
    import agentos.llm.providers.codex_native as codex_native_module
    from agentos.llm.auth.store import AuthFileStore

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: (_ for _ in ()).throw(auth_module.BrowserLaunchFailedError()),
    )
    monkeypatch.setattr(
        auth_module,
        "request_device_code",
        lambda *a, **k: (_ for _ in ()).throw(
            auth_module.AuthError("device_code_request_failed", "Could not start device sign-in.")
        ),
    )

    provider = codex_native_module.CodexNativeProvider(store=AuthFileStore(home=tmp_path))

    updates = list(provider.login_updates())

    assert updates[0]["type"] == "hint"
    assert updates[-1]["type"] == "result"
    assert updates[-1]["payload"]["authenticated"] is False


# ── bugfix regression: browser login URL/device-code must actually be shown ──


def test_login_updates_surfaces_the_real_browser_auth_url_before_waiting(tmp_path, monkeypatch):
    """Regression: `login_updates()` previously yielded a static hint with no
    URL at all ("Complete sign-in in the browser, then return here."), so
    neither the TUI nor the CLI ever showed the user anything actionable —
    this is exactly what "browser 로그인 주소가 발생하지 않음" reported. The
    first hint must now contain the real authorize URL."""
    import agentos.llm.auth.openai_codex as auth_module
    import agentos.llm.providers.codex_native as codex_native_module
    from agentos.llm.auth.store import AuthFileStore

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: (_ for _ in ()).throw(auth_module.CallbackTimeoutError()),
    )

    provider = codex_native_module.CodexNativeProvider(store=AuthFileStore(home=tmp_path))
    updates = list(provider.login_updates())

    assert updates[0]["type"] == "hint"
    assert "https://" in updates[0]["text"] or "http://" in updates[0]["text"]
    assert updates[-1]["type"] == "result"
    assert updates[-1]["payload"]["authenticated"] is False


def test_login_updates_surfaces_device_code_verification_url_and_user_code(tmp_path, monkeypatch):
    import agentos.llm.auth.openai_codex as auth_module
    import agentos.llm.providers.codex_native as codex_native_module
    from agentos.llm.auth.store import AuthFileStore

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: (_ for _ in ()).throw(auth_module.BrowserLaunchFailedError()),
    )
    monkeypatch.setattr(
        auth_module,
        "request_device_code",
        lambda *a, **k: auth_module.DeviceCode(
            verification_url="https://auth.openai.com/codex/device",
            user_code="ABCD-1234",
            device_auth_id="dev-1",
            interval=1.0,
        ),
    )
    monkeypatch.setattr(
        auth_module,
        "poll_device_code",
        lambda *a, **k: (_ for _ in ()).throw(auth_module.DeviceCodeExpiredError()),
    )

    provider = codex_native_module.CodexNativeProvider(store=AuthFileStore(home=tmp_path))
    updates = list(provider.login_updates())

    hint_texts = [u["text"] for u in updates if u["type"] == "hint"]
    assert any("https://auth.openai.com/codex/device" in text for text in hint_texts)
    assert any("ABCD-1234" in text for text in hint_texts)
    assert updates[-1]["type"] == "result"
    assert updates[-1]["payload"]["authenticated"] is False


# ── Task 3: two-request native replay regression (2026-07-26 plan) ──────────


def test_codex_native_two_request_replay_includes_function_call_and_output_for_list_success():
    """Regression: fake Codex-native provider, two requests.

    First response emits a `list` function_call with call_id. The second
    request must contain the matching function_call + function_call_output
    pair with the same call_id, and the output must carry the tool result
    (success path).
    """
    invocation_request_second_turn = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="list files"),
            InvocationMessage(
                role="tool",
                text="README.md\nagentos/\ntests/",
                metadata={"call_id": "call_list_success", "name": "list", "arguments": '{"path":"."}'},
            ),
        ]
    )
    body = build_transport_request(
        model="gpt-5-codex", invocation_request=invocation_request_second_turn
    ).to_request_body()

    input_items = body["input"]
    # Must contain user message, then function_call, then function_call_output
    assert {"role": "user", "content": "list files"} in input_items
    fc_items = [i for i in input_items if i.get("type") == "function_call"]
    fco_items = [i for i in input_items if i.get("type") == "function_call_output"]
    assert len(fc_items) == 1
    assert len(fco_items) == 1
    assert fc_items[0]["call_id"] == "call_list_success"
    assert fc_items[0]["name"] == "list"
    assert fc_items[0]["arguments"] == '{"path":"."}'
    assert fco_items[0]["call_id"] == "call_list_success"
    assert "README.md" in fco_items[0]["output"]
    # function_call must come before function_call_output
    fc_index = input_items.index(fc_items[0])
    fco_index = input_items.index(fco_items[0])
    assert fc_index < fco_index


def test_codex_native_two_request_replay_includes_function_call_and_output_for_list_error():
    """Regression: same as success path but with an error result.

    Error output (e.g. 'Error: not a directory') must be preserved in
    function_call_output, not silenced.
    """
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="list /notadir"),
            InvocationMessage(
                role="tool",
                text="Error: not a directory: /notadir",
                metadata={"call_id": "call_list_err", "name": "list", "arguments": '{"path":"/notadir"}'},
            ),
        ]
    )
    body = build_transport_request(
        model="gpt-5-codex", invocation_request=invocation_request
    ).to_request_body()

    fco_items = [i for i in body["input"] if i.get("type") == "function_call_output"]
    assert len(fco_items) == 1
    assert fco_items[0]["call_id"] == "call_list_err"
    assert "Error" in fco_items[0]["output"]
    assert "not a directory" in fco_items[0]["output"]


def test_codex_native_two_request_replay_no_orphan_output_without_function_call():
    """Regression: legacy tool messages (no call_id) must be silently excluded.

    Sending a function_call_output without its matching function_call in the
    same input is invalid for the Codex backend. Legacy messages with no
    correlation data must be dropped entirely from the request body.
    """
    invocation_request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="continue"),
            # Legacy tool message: no call_id/name/arguments
            InvocationMessage(role="tool", text="old result with no correlation"),
        ]
    )
    body = build_transport_request(
        model="gpt-5-codex", invocation_request=invocation_request
    ).to_request_body()

    # Neither function_call nor function_call_output must appear
    for item in body["input"]:
        assert item.get("type") not in ("function_call", "function_call_output")
    assert body["input"] == [{"role": "user", "content": "continue"}]
