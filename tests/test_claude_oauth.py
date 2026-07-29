from __future__ import annotations

import json
import os
import threading
import urllib.parse
import urllib.request

import pytest

from agentos.llm.auth import anthropic_claude as auth_module
from agentos.llm.auth.anthropic_claude import (
    TokenResult,
    build_authorize_url,
    classify_auth_failure,
    is_access_token_expired,
    logout,
    persist_tokens,
    refresh_access_token,
    resolve_status,
    run_browser_login,
)
from agentos.llm.auth.openai_codex import AuthError, BrowserLaunchFailedError, StateMismatchError, generate_pkce, generate_state
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.auth.types import AuthRecord

SENTINEL = os.environ.get("AGENTOS_TEST_SECRET", "sk-ant-oat-test-secret-value")


@pytest.fixture(autouse=True)
def _use_ephemeral_callback_port(monkeypatch):
    """These tests exercise the real local callback `HTTPServer`, but must
    not depend on the actual fixed port (53692) being free on the host —
    it's a single shared port with no fallback now (see
    `test_require_fixed_port_raises_when_port_is_busy` in
    test_codex_oauth.py), so any other process (or a stuck previous run)
    holding it would make these tests flaky. `port=0` asks the OS for any
    free port instead."""
    monkeypatch.setattr(auth_module, "DEFAULT_CALLBACK_PORT", 0)


class FakeTransport:
    def __init__(self, *, browser_opens: bool = True, token_payload: dict | None = None):
        self.browser_opens = browser_opens
        self.token_payload = token_payload or {
            "access_token": SENTINEL,
            "refresh_token": SENTINEL,
        }
        self.opened_urls: list[str] = []
        self.posted: list[tuple[str, dict]] = []

    def open_browser(self, url: str) -> bool:
        self.opened_urls.append(url)
        return self.browser_opens

    def post_json(self, url: str, payload: dict) -> dict:
        self.posted.append((url, payload))
        return dict(self.token_payload)


def _fire_callback(port: int, *, state: str, code: str | None = "auth-code-123", error: str | None = None) -> None:
    params = {"state": state}
    if code is not None:
        params["code"] = code
    if error is not None:
        params["error"] = error
    query = urllib.parse.urlencode(params)
    url = f"http://127.0.0.1:{port}/callback?{query}"
    urllib.request.urlopen(url, timeout=5).read()  # noqa: S310


def test_prepare_browser_login_redirect_uri_uses_callback_not_auth_callback():
    """Regression: this previously built redirect_uri as
    "http://localhost:{port}/auth/callback" (Codex's convention, reused by
    copy-paste), but Anthropic's OAuth client only has "/callback"
    registered (see pi's anthropic.ts CALLBACK_PATH) — so login always
    failed with "Redirect URI ... is not supported by client", even on the
    otherwise-correct port."""
    import agentos.llm.auth.anthropic_claude as claude_auth

    prepared = claude_auth.prepare_browser_login()
    try:
        assert prepared._redirect_uri.endswith("/callback")
        assert not prepared._redirect_uri.endswith("/auth/callback")
    finally:
        prepared._server.server_close()


# --- pkce / authorize url ---


def test_build_authorize_url_includes_pkce_state_and_scopes():
    pkce = generate_pkce()
    state = generate_state()
    url = build_authorize_url(
        authorize_url="https://claude.ai/oauth/authorize",
        client_id="client-123",
        redirect_uri="http://localhost:53692/callback",
        state=state,
        pkce=pkce,
    )
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert f"state={state}" in url
    assert "client_id=client-123" in url
    assert "scope=" in url


def test_build_authorize_url_includes_code_true_param():
    """Regression: without `code=true`, Anthropic's authorize endpoint treats
    the request as an in-page "connect this app" approval that never
    redirects anywhere — after clicking Allow, the browser just keeps
    spinning on claude.ai instead of navigating to redirect_uri. `code=true`
    (per pi's anthropic.ts) is what makes it perform the actual
    authorization-code redirect a CLI loopback flow needs."""
    url = build_authorize_url(
        authorize_url="https://claude.ai/oauth/authorize",
        client_id="client-123",
        redirect_uri="http://localhost:53692/callback",
        state=generate_state(),
        pkce=generate_pkce(),
    )
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert query["code"] == ["true"]


# --- browser login: success / state mismatch / browser failure ---


def test_callback_completes_login_and_exchanges_tokens():
    transport = FakeTransport()
    result_holder: dict = {}

    def do_login():
        result_holder["result"] = run_browser_login(transport=transport, timeout_seconds=5)

    thread = threading.Thread(target=do_login)
    thread.start()

    for _ in range(200):
        if transport.opened_urls:
            break
        threading.Event().wait(0.01)
    assert transport.opened_urls, "browser open was not invoked"
    auth_url = transport.opened_urls[0]

    parsed = urllib.parse.urlparse(auth_url)
    query = urllib.parse.parse_qs(parsed.query)
    state = query["state"][0]
    redirect_uri = urllib.parse.urlparse(query["redirect_uri"][0])
    port = redirect_uri.port

    _fire_callback(port, state=state)
    thread.join(timeout=5)

    result: TokenResult = result_holder["result"]
    assert result.access_token == SENTINEL
    assert result.refresh_token == SENTINEL


def test_state_mismatch_raises_state_mismatch_error():
    transport = FakeTransport()
    result_holder: dict = {}
    error_holder: dict = {}

    def do_login():
        try:
            result_holder["result"] = run_browser_login(transport=transport, timeout_seconds=5)
        except AuthError as exc:
            error_holder["error"] = exc

    thread = threading.Thread(target=do_login)
    thread.start()
    for _ in range(200):
        if transport.opened_urls:
            break
        threading.Event().wait(0.01)

    parsed = urllib.parse.urlparse(transport.opened_urls[0])
    query = urllib.parse.parse_qs(parsed.query)
    redirect_uri = urllib.parse.urlparse(query["redirect_uri"][0])
    port = redirect_uri.port

    _fire_callback(port, state="wrong-state")
    thread.join(timeout=5)

    assert isinstance(error_holder.get("error"), StateMismatchError)


def test_browser_failure_raises_browser_launch_failed_error():
    transport = FakeTransport(browser_opens=False)
    with pytest.raises(BrowserLaunchFailedError):
        run_browser_login(transport=transport, timeout_seconds=1)


def test_callback_timeout_raises_callback_timeout_error():
    from agentos.llm.auth.openai_codex import CallbackTimeoutError

    transport = FakeTransport()
    with pytest.raises(CallbackTimeoutError):
        run_browser_login(transport=transport, timeout_seconds=0.05, open_browser=False)


# --- token exchange failure ---


def test_token_exchange_failure_raises_auth_error():
    class FailingTransport:
        def open_browser(self, url: str) -> bool:
            return True

        def post_json(self, url: str, payload: dict) -> dict:
            raise OSError("token endpoint unreachable")

    with pytest.raises(AuthError) as exc_info:
        run_browser_login(transport=FailingTransport(), timeout_seconds=5)
    assert exc_info.value.code in ("token_exchange_failed", "callback_timeout")


# --- refresh / expired / logout / status resolution ---


class RefreshTransport:
    def __init__(self, *, new_access_token: str = "new-access-token"):
        self.new_access_token = new_access_token
        self.refresh_calls: list[dict] = []

    def open_browser(self, url: str) -> bool:
        return True

    def post_json(self, url: str, payload: dict) -> dict:
        self.refresh_calls.append(payload)
        return {
            "access_token": self.new_access_token,
            "refresh_token": "rotated-refresh-token",
            "expires_in": 3600,
        }


def test_refresh_access_token_exchanges_refresh_token_for_new_tokens():
    transport = RefreshTransport()
    result = refresh_access_token("old-refresh-token", transport=transport)
    assert result.access_token == "new-access-token"
    assert transport.refresh_calls[0]["grant_type"] == "refresh_token"
    assert transport.refresh_calls[0]["refresh_token"] == "old-refresh-token"


def test_is_access_token_expired_true_when_past_expiry():
    record = AuthRecord(
        provider="claude",
        credential_type="account-login",
        authenticated=True,
        metadata={"expires_at": 100.0},
    )
    assert is_access_token_expired(record, now=200.0) is True


def test_is_access_token_expired_false_when_before_expiry():
    record = AuthRecord(
        provider="claude",
        credential_type="account-login",
        authenticated=True,
        metadata={"expires_at": 300.0},
    )
    assert is_access_token_expired(record, now=200.0) is False


def test_expired_access_token_triggers_transparent_refresh(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(
        TokenResult(access_token="stale-access-token", refresh_token="refresh-token-1", expires_in=-10),
        store=store,
    )
    transport = RefreshTransport()
    status = resolve_status(store, transport=transport)
    assert status.authenticated is True
    assert status.refreshed is True
    assert store.get("claude").secrets["access_token"] == "new-access-token"


def test_status_resolution_returns_unauthenticated_when_no_record(tmp_path):
    store = AuthFileStore(home=tmp_path)
    status = resolve_status(store)
    assert status.authenticated is False
    assert status.status == "unauthenticated"


def test_logout_deletes_record_and_is_idempotent(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token=SENTINEL, refresh_token=SENTINEL), store=store)
    assert logout(store) is True
    assert store.get("claude") is None
    assert logout(store) is False


# --- classify_auth_failure: single-frame, no cross-request state ---


def test_classify_auth_failure_authentication_error_is_token_expired():
    assert classify_auth_failure("authentication_error", 401) == "token_expired"


def test_classify_auth_failure_missing_error_type_is_integration_blocked():
    assert classify_auth_failure(None, 401) == "claude_integration_blocked"


def test_classify_auth_failure_other_error_type_is_integration_blocked():
    assert classify_auth_failure("some_other_type", 403) == "claude_integration_blocked"


# --- secret / redaction ---


def test_persist_tokens_never_leaks_raw_secret_in_summary(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(TokenResult(access_token=SENTINEL, refresh_token=SENTINEL), store=store)
    summary_json = json.dumps(store.get("claude").summary().to_dict())
    assert SENTINEL not in summary_json


def test_refresh_failure_error_message_has_no_raw_secret():
    class FailingTransport:
        def open_browser(self, url: str) -> bool:
            return True

        def post_json(self, url: str, payload: dict) -> dict:
            raise OSError(f"network error near token {SENTINEL}")

    with pytest.raises(AuthError) as exc_info:
        refresh_access_token(SENTINEL, transport=FailingTransport())
    assert SENTINEL not in str(exc_info.value)
    assert SENTINEL not in exc_info.value.message


def test_state_mismatch_error_message_has_no_callback_query():
    error = StateMismatchError()
    assert "state=" not in str(error)
    assert "code=" not in str(error)


def test_resolve_status_does_not_leak_refresh_token_on_failure(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(
        TokenResult(access_token="stale", refresh_token=SENTINEL, expires_in=-10),
        store=store,
    )

    class FailingRefreshTransport:
        def open_browser(self, url: str) -> bool:
            return True

        def post_json(self, url: str, payload: dict) -> dict:
            raise OSError("refresh endpoint unreachable")

    status = resolve_status(store, transport=FailingRefreshTransport())
    assert status.authenticated is False
    assert SENTINEL not in str(status)
