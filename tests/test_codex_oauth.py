from __future__ import annotations

import json
import os
import threading
import urllib.request

import pytest

from agentos.llm.auth import openai_codex as auth_module
from agentos.llm.auth.openai_codex import (
    AuthError,
    BrowserLaunchFailedError,
    DeviceCodeCancelledError,
    DeviceCodeExpiredError,
    StateMismatchError,
    TokenResult,
    _PendingAuthorization,
    build_authorize_url,
    generate_pkce,
    generate_state,
    is_access_token_expired,
    logout,
    persist_tokens,
    poll_device_code,
    refresh_access_token,
    request_device_code,
    resolve_status,
    run_browser_login,
)
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.auth.types import AuthRecord

SENTINEL = os.environ.get("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")


class FakeTransport:
    def __init__(self, *, browser_opens: bool = True, token_payload: dict | None = None):
        self.browser_opens = browser_opens
        self.token_payload = token_payload or {
            "id_token": SENTINEL,
            "access_token": SENTINEL,
            "refresh_token": SENTINEL,
            "account_label": "user@example.com",
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
    import urllib.parse

    params = {"state": state}
    if code is not None:
        params["code"] = code
    if error is not None:
        params["error"] = error
    query = urllib.parse.urlencode(params)
    url = f"http://127.0.0.1:{port}/auth/callback?{query}"
    urllib.request.urlopen(url, timeout=5).read()  # noqa: S310


# --- pkce / callback / state_mismatch / browser_failure ---


def test_pkce_generates_verifier_and_s256_challenge():
    pkce = generate_pkce()
    assert 43 <= len(pkce.code_verifier) <= 128
    assert pkce.code_challenge != pkce.code_verifier


def test_pkce_is_random_per_call():
    a = generate_pkce()
    b = generate_pkce()
    assert a.code_verifier != b.code_verifier


def test_build_authorize_url_includes_pkce_and_state():
    pkce = generate_pkce()
    state = generate_state()
    url = build_authorize_url(
        issuer="https://auth.example.com",
        client_id="client-123",
        redirect_uri="http://localhost:1455/auth/callback",
        state=state,
        pkce=pkce,
    )
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert f"state={state}" in url
    assert "client_id=client-123" in url


def test_callback_completes_login_and_exchanges_tokens():
    transport = FakeTransport()
    result_holder: dict = {}

    def do_login():
        result_holder["result"] = run_browser_login(transport=transport, timeout_seconds=5)

    thread = threading.Thread(target=do_login)
    thread.start()

    # Wait for the server to publish the auth URL via opened_urls, then fire callback.
    for _ in range(200):
        if transport.opened_urls:
            break
        threading.Event().wait(0.01)
    assert transport.opened_urls, "browser open was not invoked"
    auth_url = transport.opened_urls[0]
    import urllib.parse

    parsed = urllib.parse.urlparse(auth_url)
    query = urllib.parse.parse_qs(parsed.query)
    state = query["state"][0]
    redirect_uri = urllib.parse.urlparse(query["redirect_uri"][0])
    port = redirect_uri.port

    _fire_callback(port, state=state)
    thread.join(timeout=5)

    result: TokenResult = result_holder["result"]
    assert result.access_token == SENTINEL
    assert result.account_label == "user@example.com"


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
    import urllib.parse

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


# --- device_code / slow_down / pending / cancel ---


class DeviceCodeTransport:
    def __init__(self, *, pending_polls: int = 0, interval: float = 0.01):
        self.pending_polls = pending_polls
        self.interval = interval
        self.poll_count = 0

    def open_browser(self, url: str) -> bool:
        return True

    def post_json(self, url: str, payload: dict) -> dict:
        if "usercode" in url:
            return {
                "device_auth_id": "device-auth-1",
                "user_code": "ABCD-1234",
                "interval": self.interval,
            }
        if "deviceauth/token" in url:
            self.poll_count += 1
            if self.poll_count <= self.pending_polls:
                raise _PendingAuthorization()
            return {
                "authorization_code": "auth-code-device",
                "code_challenge": "challenge",
                "code_verifier": "verifier",
            }
        if "oauth/token" in url:
            return {
                "id_token": SENTINEL,
                "access_token": SENTINEL,
                "refresh_token": SENTINEL,
            }
        raise AssertionError(f"unexpected url {url}")


def test_device_code_request_returns_verification_url_and_user_code():
    transport = DeviceCodeTransport()
    code = request_device_code(transport=transport)
    assert code.user_code == "ABCD-1234"
    assert code.verification_url.endswith("/codex/device")


def test_device_code_slow_down_interval_is_honored_between_polls():
    transport = DeviceCodeTransport(pending_polls=2, interval=0.01)
    code = request_device_code(transport=transport)
    result = poll_device_code(code, transport=transport)
    assert transport.poll_count == 3
    assert result.access_token == SENTINEL


def test_device_code_pending_status_retries_until_success():
    transport = DeviceCodeTransport(pending_polls=1, interval=0.01)
    code = request_device_code(transport=transport)
    result = poll_device_code(code, transport=transport)
    assert isinstance(result, TokenResult)


def test_device_code_cancel_raises_device_code_cancelled_error():
    transport = DeviceCodeTransport(pending_polls=1000, interval=0.01)
    code = request_device_code(transport=transport)
    cancel_event = threading.Event()
    cancel_event.set()
    with pytest.raises(DeviceCodeCancelledError):
        poll_device_code(code, transport=transport, cancel_event=cancel_event)


def test_device_code_expires_after_max_wait():
    transport = DeviceCodeTransport(pending_polls=1000, interval=0.01)
    code = request_device_code(transport=transport)
    with pytest.raises(DeviceCodeExpiredError):
        poll_device_code(code, transport=transport, max_wait_seconds=0.02)


def test_device_code_never_leaks_raw_tokens_in_exception_text():
    transport = DeviceCodeTransport(pending_polls=1000, interval=0.01)
    code = request_device_code(transport=transport)
    try:
        poll_device_code(code, transport=transport, max_wait_seconds=0.01)
    except DeviceCodeExpiredError as exc:
        assert SENTINEL not in str(exc)


# --- refresh / expired / logout / status_resolution ---


class RefreshTransport:
    def __init__(self, *, new_access_token: str = "new-access-token"):
        self.new_access_token = new_access_token
        self.refresh_calls: list[dict] = []

    def open_browser(self, url: str) -> bool:
        return True

    def post_json(self, url: str, payload: dict) -> dict:
        self.refresh_calls.append(payload)
        return {
            "id_token": SENTINEL,
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
        provider="codex",
        credential_type="account-login",
        authenticated=True,
        metadata={"expires_at": 100.0},
    )
    assert is_access_token_expired(record, now=200.0) is True


def test_is_access_token_expired_false_when_before_expiry():
    record = AuthRecord(
        provider="codex",
        credential_type="account-login",
        authenticated=True,
        metadata={"expires_at": 300.0},
    )
    assert is_access_token_expired(record, now=200.0) is False


def test_expired_access_token_triggers_transparent_refresh(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(
        TokenResult(
            id_token=SENTINEL,
            access_token="stale-access-token",
            refresh_token="refresh-token-1",
            expires_in=-10,
        ),
        store=store,
    )
    transport = RefreshTransport()
    status = resolve_status(store, transport=transport)
    assert status.authenticated is True
    assert status.refreshed is True
    assert store.get("codex").secrets["access_token"] == "new-access-token"


def test_status_resolution_returns_unauthenticated_when_no_record(tmp_path):
    store = AuthFileStore(home=tmp_path)
    status = resolve_status(store)
    assert status.authenticated is False
    assert status.status == "unauthenticated"


def test_logout_deletes_record_and_is_idempotent(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(
        TokenResult(id_token=SENTINEL, access_token=SENTINEL, refresh_token=SENTINEL),
        store=store,
    )
    assert logout(store) is True
    assert store.get("codex") is None
    assert logout(store) is False


# --- secret / redact / stderr / callback ---


def test_persist_tokens_never_leaks_raw_secret_in_summary(tmp_path):
    store = AuthFileStore(home=tmp_path)
    persist_tokens(
        TokenResult(id_token=SENTINEL, access_token=SENTINEL, refresh_token=SENTINEL),
        store=store,
    )
    summary_json = json.dumps(store.get("codex").summary().to_dict())
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
        TokenResult(
            id_token=SENTINEL,
            access_token="stale",
            refresh_token=SENTINEL,
            expires_in=-10,
        ),
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
