from __future__ import annotations

import os

from agentos.llm.auth.anthropic_claude import TokenResult, persist_tokens
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.providers.claude_native import ClaudeNativeProvider
from agentos.llm.registry import supported_providers
from agentos.llm.transports.base import ProviderEvent, TransportError
from agentos.llm.types import InvocationMessage, InvocationRequest, ProviderCapabilities

SENTINEL = os.environ.get("AGENTOS_TEST_SECRET", "sk-ant-oat-test-secret-value")


def test_claude_is_registered_as_supported_provider():
    assert "claude" in supported_providers()
    assert supported_providers() == ("claude", "codex", "codex-cli", "mock")


def test_claude_native_provider_declares_context_aware_no_continuation():
    capabilities = ClaudeNativeProvider().capabilities()
    assert capabilities == ProviderCapabilities(context_aware=True, supports_continuation=False)


def test_status_unauthenticated_when_no_record(tmp_path):
    provider = ClaudeNativeProvider(store=AuthFileStore(home=tmp_path))
    status = provider.status()
    assert status.authenticated is False
    assert status.message == "AgentOS-owned Claude sign-in is required."
    assert status.recovery == "Run: agentos llm login --provider claude"


def test_status_authenticated_after_persisted_tokens(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600), store=store)
    provider = ClaudeNativeProvider(store=store)
    status = provider.status()
    assert status.authenticated is True
    assert status.message == "Signed in with Claude account-login."


def test_login_persists_tokens_on_success(tmp_path, monkeypatch):
    import agentos.llm.auth.anthropic_claude as auth_module

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600),
    )

    store = AuthFileStore(home=tmp_path)
    provider = ClaudeNativeProvider(store=store)
    status = provider.login()

    assert status.authenticated is True
    assert status.message == "Claude sign-in completed."
    assert store.get("claude").secrets["access_token"] == "access-1"


def test_login_failure_returns_sanitized_status_not_exception(tmp_path, monkeypatch):
    import agentos.llm.auth.anthropic_claude as auth_module

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: (_ for _ in ()).throw(auth_module.BrowserLaunchFailedError()),
    )

    provider = ClaudeNativeProvider(store=AuthFileStore(home=tmp_path))
    status = provider.login()

    assert status.authenticated is False
    assert status.status == "failed"
    assert status.recovery == "Run: agentos llm login --provider claude"


def test_login_updates_surfaces_the_real_browser_auth_url_before_waiting(tmp_path, monkeypatch):
    import agentos.llm.auth.anthropic_claude as auth_module

    monkeypatch.setattr(
        auth_module,
        "complete_browser_login",
        lambda prepared, **kwargs: (_ for _ in ()).throw(auth_module.CallbackTimeoutError()),
    )

    provider = ClaudeNativeProvider(store=AuthFileStore(home=tmp_path))
    updates = list(provider.login_updates())

    assert updates[0]["type"] == "hint"
    assert "https://" in updates[0]["text"]
    assert updates[-1]["type"] == "result"
    assert updates[-1]["payload"]["authenticated"] is False


def test_logout_reports_logged_out_and_is_idempotent(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1"), store=store)
    provider = ClaudeNativeProvider(store=store)

    first = provider.logout()
    second = provider.logout()

    assert first.status == "logged_out"
    assert first.message == "Claude sign-out completed."
    assert second.message == "Claude was already signed out."


def test_stream_once_yields_unauthenticated_error_when_no_credentials(tmp_path):
    provider = ClaudeNativeProvider(store=AuthFileStore(home=tmp_path))
    events = list(provider.stream_once("hello"))
    assert len(events) == 1
    assert events[0].type == "error"
    assert events[0].error["code"] == "unauthenticated"


def test_stream_context_yields_normalized_events_from_transport(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600), store=store)

    class FakeTransport:
        def stream(self, request):
            yield ProviderEvent(type="start")
            yield ProviderEvent(type="message_delta", text="hi")
            yield ProviderEvent(type="done", usage={"input_tokens": 1, "output_tokens": 1})

    provider = ClaudeNativeProvider(store=store, transport_factory=lambda token: FakeTransport())
    request = InvocationRequest(messages=[InvocationMessage(role="user", text="hello")])

    events = list(provider.stream_context(request))

    assert [event.type for event in events] == ["start", "message_delta", "done"]
    assert events[1].text == "hi"


def test_token_expired_error_uses_standard_recovery_message(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600), store=store)

    class FakeTransport:
        def stream(self, request):
            yield ProviderEvent(type="start")
            yield ProviderEvent(type="error", error={"code": "token_expired", "message": "expired"})

    provider = ClaudeNativeProvider(store=store, transport_factory=lambda token: FakeTransport())
    request = InvocationRequest(messages=[InvocationMessage(role="user", text="hello")])

    events = list(provider.stream_context(request))

    error_event = events[-1]
    assert error_event.type == "error"
    assert error_event.error["code"] == "token_expired"
    assert error_event.recovery == "Run: agentos llm login --provider claude"


def test_claude_integration_blocked_error_uses_distinct_recovery_message(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600), store=store)

    class FakeTransport:
        def stream(self, request):
            yield ProviderEvent(type="start")
            yield ProviderEvent(type="error", error={"code": "claude_integration_blocked", "message": "blocked"})

    provider = ClaudeNativeProvider(store=store, transport_factory=lambda token: FakeTransport())
    request = InvocationRequest(messages=[InvocationMessage(role="user", text="hello")])

    events = list(provider.stream_context(request))

    error_event = events[-1]
    assert error_event.type == "error"
    assert error_event.error["code"] == "claude_integration_blocked"
    assert error_event.recovery != "Run: agentos llm login --provider claude"
    assert "AgentOS update" in error_event.recovery


def test_stream_via_native_provider_transport_error_diagnostics_never_expose_sentinel(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", SENTINEL)
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token="access-1", refresh_token="refresh-1", expires_in=3600), store=store)

    class FailingTransport:
        def stream(self, request):
            raise TransportError("boom", f"native transport failure: {SENTINEL}", retryable=True)
            yield  # pragma: no cover - makes this a generator function

    provider = ClaudeNativeProvider(store=store, transport_factory=lambda token: FailingTransport())
    request = InvocationRequest(messages=[InvocationMessage(role="user", text="hello")])

    events = list(provider.stream_context(request))
    serialized = "".join(str(vars(e)) for e in events)

    assert events[-1].type == "error"
    assert SENTINEL not in serialized
