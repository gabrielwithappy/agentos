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
