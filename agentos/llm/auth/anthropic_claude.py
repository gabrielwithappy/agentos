from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.parse
from dataclasses import dataclass
from http.server import HTTPServer
from typing import Any

from agentos.llm.auth.openai_codex import (
    AuthError,
    BrowserLaunchFailedError,
    CallbackPortUnavailableError,
    CallbackTimeoutError,
    HttpTransport,
    PkceCodes,
    StateMismatchError,
    UrllibHttpTransport,
    _CallbackResult,
    _make_callback_handler,
    _require_fixed_port,
    generate_pkce,
    generate_state,
)
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.auth.types import AuthRecord

DEFAULT_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
DEFAULT_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"  # gitleaks:allow — Anthropic's public OAuth client_id (no client_secret), matches the Claude Code CLI's; not a secret
SCOPES = "org:create_api_key user:profile user:inference user:sessions:claude_code user:mcp_servers user:file_upload"
DEFAULT_CALLBACK_PORT = 53692
CALLBACK_PATH = "/callback"
AUTH_PROVIDER_NAME = "claude"
CREDENTIAL_TYPE = "account-login"
_REFRESH_LOCK = threading.Lock()


def _env_authorize_url() -> str:
    return os.environ.get("AGENTOS_CLAUDE_AUTHORIZE_URL", DEFAULT_AUTHORIZE_URL)


def _env_token_url() -> str:
    return os.environ.get("AGENTOS_CLAUDE_TOKEN_URL", DEFAULT_TOKEN_URL)


def _env_client_id() -> str:
    return os.environ.get("AGENTOS_CLAUDE_CLIENT_ID", CLIENT_ID)


@dataclass(frozen=True)
class TokenResult:
    access_token: str
    refresh_token: str
    expires_in: float | None = None


def build_authorize_url(*, authorize_url: str, client_id: str, redirect_uri: str, state: str, pkce: PkceCodes) -> str:
    params = {
        # Anthropic's authorize endpoint otherwise treats this as an in-page
        # "connect this app" approval that never redirects anywhere — the
        # browser stays on the approval page after clicking Allow instead of
        # navigating to redirect_uri, which is exactly the "계속 스피닝" symptom.
        # `code=true` (per pi's anthropic.ts) is what makes it perform the
        # actual authorization-code redirect a CLI loopback flow needs.
        "code": "true",
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
        "code_challenge": pkce.code_challenge,
        "code_challenge_method": "S256",
    }
    query = urllib.parse.urlencode(params)
    return f"{authorize_url}?{query}"


@dataclass(frozen=True)
class PreparedBrowserLogin:
    """Mirrors `openai_codex.PreparedBrowserLogin`: the authorize URL is
    already built and the local callback server already bound, but not yet
    launched or waited on — see that class's docstring for the rationale."""

    auth_url: str
    _server: HTTPServer
    _result: _CallbackResult
    _redirect_uri: str
    _pkce: PkceCodes
    _token_url: str
    _client_id: str


def prepare_browser_login(
    *,
    authorize_url: str | None = None,
    token_url: str | None = None,
    client_id: str | None = None,
) -> PreparedBrowserLogin:
    resolved_authorize_url = authorize_url or _env_authorize_url()
    resolved_token_url = token_url or _env_token_url()
    resolved_client_id = client_id or _env_client_id()

    port = _require_fixed_port(DEFAULT_CALLBACK_PORT)
    # Anthropic's registered redirect_uri path is "/callback", not "/auth/callback"
    # (that's Codex's convention) — see pi's anthropic.ts CALLBACK_PATH. Using the
    # wrong path is exactly what produces "Redirect URI ... is not supported by
    # client" even when the host/port are otherwise correct.
    redirect_uri = f"http://localhost:{port}{CALLBACK_PATH}"
    pkce = generate_pkce()
    state = generate_state()

    result = _CallbackResult()
    handler_cls = _make_callback_handler(state, result, callback_path=CALLBACK_PATH)
    server = HTTPServer(("127.0.0.1", port), handler_cls)

    auth_url = build_authorize_url(
        authorize_url=resolved_authorize_url,
        client_id=resolved_client_id,
        redirect_uri=redirect_uri,
        state=state,
        pkce=pkce,
    )

    return PreparedBrowserLogin(
        auth_url=auth_url,
        _server=server,
        _result=result,
        _redirect_uri=redirect_uri,
        _pkce=pkce,
        _token_url=resolved_token_url,
        _client_id=resolved_client_id,
    )


def complete_browser_login(
    prepared: PreparedBrowserLogin,
    *,
    transport: HttpTransport | None = None,
    timeout_seconds: float = 300.0,
    open_browser: bool = True,
) -> TokenResult:
    http = transport or UrllibHttpTransport()
    server = prepared._server
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    if open_browser:
        opened = http.open_browser(prepared.auth_url)
        if not opened:
            server.server_close()
            raise BrowserLaunchFailedError()

    completed = prepared._result.event.wait(timeout=timeout_seconds)
    server.server_close()

    if not completed:
        raise CallbackTimeoutError()
    if prepared._result.error == "state_mismatch":
        raise StateMismatchError()
    if prepared._result.error:
        raise AuthError("callback_error", "Sign-in failed during the browser callback.")
    if not prepared._result.code:
        raise AuthError("callback_missing_code", "Sign-in callback did not include an authorization code.")

    return _exchange_code_for_tokens(
        http,
        token_url=prepared._token_url,
        client_id=prepared._client_id,
        redirect_uri=prepared._redirect_uri,
        pkce=prepared._pkce,
        state=prepared._result.state,
        authorization_code=prepared._result.code,
    )


def run_browser_login(
    *,
    transport: HttpTransport | None = None,
    authorize_url: str | None = None,
    token_url: str | None = None,
    client_id: str | None = None,
    timeout_seconds: float = 300.0,
    open_browser: bool = True,
) -> TokenResult:
    prepared = prepare_browser_login(authorize_url=authorize_url, token_url=token_url, client_id=client_id)
    return complete_browser_login(
        prepared, transport=transport, timeout_seconds=timeout_seconds, open_browser=open_browser
    )


def _exchange_code_for_tokens(
    http: HttpTransport,
    *,
    token_url: str,
    client_id: str,
    redirect_uri: str,
    pkce: PkceCodes,
    state: str | None,
    authorization_code: str,
) -> TokenResult:
    try:
        payload = http.post_json(
            token_url,
            {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": authorization_code,
                "state": state,
                "redirect_uri": redirect_uri,
                "code_verifier": pkce.code_verifier,
            },
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise AuthError("token_exchange_failed", "Token exchange failed.", retryable=True) from exc
    return _token_result_from_payload(payload)


def _token_result_from_payload(payload: dict[str, Any]) -> TokenResult:
    try:
        return TokenResult(
            access_token=str(payload["access_token"]),
            refresh_token=str(payload["refresh_token"]),
            expires_in=float(payload["expires_in"]) if payload.get("expires_in") is not None else None,
        )
    except KeyError as exc:
        raise AuthError("token_response_invalid", "Sign-in response was missing required fields.") from exc


def _expiry_timestamp(expires_in: float | None) -> float | None:
    if expires_in is None:
        return None
    return time.time() + expires_in


def persist_tokens(
    tokens: TokenResult,
    *,
    store: AuthFileStore,
) -> AuthRecord:
    """Persist native Claude tokens to the local auth store.

    Only `store`-managed secrets carry token values; callers must not log
    or render `tokens` directly.
    """
    record = AuthRecord(
        provider=AUTH_PROVIDER_NAME,
        credential_type=CREDENTIAL_TYPE,
        authenticated=True,
        secrets={
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
        },
        account_label=None,
        metadata={"expires_at": _expiry_timestamp(tokens.expires_in)},
    )
    return store.upsert(record)


def refresh_access_token(
    refresh_token: str,
    *,
    transport: HttpTransport | None = None,
    token_url: str | None = None,
    client_id: str | None = None,
) -> TokenResult:
    """Exchange a stored refresh token for a fresh access token.

    Serializes concurrent refreshes for the same process via `_REFRESH_LOCK`,
    mirroring `openai_codex.refresh_access_token()`.
    """
    resolved_token_url = token_url or _env_token_url()
    resolved_client_id = client_id or _env_client_id()
    http = transport or UrllibHttpTransport()

    with _REFRESH_LOCK:
        try:
            payload = http.post_json(
                resolved_token_url,
                {
                    "grant_type": "refresh_token",
                    "client_id": resolved_client_id,
                    "refresh_token": refresh_token,
                },
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise AuthError("refresh_failed", "Session refresh failed.", retryable=True) from exc

    return _token_result_from_payload(payload)


def is_access_token_expired(record: AuthRecord, *, now: float | None = None) -> bool:
    expires_at = record.metadata.get("expires_at")
    if expires_at is None:
        return False
    current = now if now is not None else time.time()
    return current >= float(expires_at)


@dataclass(frozen=True)
class ResolvedStatus:
    authenticated: bool
    status: str
    account_label: str | None = None
    refreshed: bool = False


def resolve_status(
    store: AuthFileStore,
    *,
    transport: HttpTransport | None = None,
    token_url: str | None = None,
    client_id: str | None = None,
    now: float | None = None,
) -> ResolvedStatus:
    """Resolve current auth status, refreshing an expired access token
    transparently when a refresh token is available. Never returns or logs
    a raw token value."""
    record = store.get(AUTH_PROVIDER_NAME)
    if record is None or not record.authenticated:
        return ResolvedStatus(authenticated=False, status="unauthenticated")

    if not is_access_token_expired(record, now=now):
        return ResolvedStatus(
            authenticated=True,
            status="authenticated",
            account_label=record.account_label,
        )

    refresh_token = record.secrets.get("refresh_token")
    if not refresh_token:
        return ResolvedStatus(authenticated=False, status="expired")

    try:
        refreshed_tokens = refresh_access_token(
            refresh_token,
            transport=transport,
            token_url=token_url,
            client_id=client_id,
        )
    except AuthError:
        return ResolvedStatus(authenticated=False, status="expired")

    persist_tokens(refreshed_tokens, store=store)
    return ResolvedStatus(
        authenticated=True,
        status="authenticated",
        account_label=record.account_label,
        refreshed=True,
    )


def logout(store: AuthFileStore) -> bool:
    """Delete the local native Claude auth record. Idempotent: returns True
    only when a record was actually removed."""
    return store.delete(AUTH_PROVIDER_NAME)


def classify_auth_failure(error_type: str | None, status_code: int) -> str:
    """Distinguish a normal expired/revoked OAuth token from Anthropic
    blocking the Claude-Code-impersonation integration pattern entirely.

    Decided from a single error response (status code + `error.type`); no
    cross-request state or retry counting is needed or used. Anthropic has
    not published a dedicated error type for rejecting the impersonation
    headers, so any 401/403 that isn't the documented `authentication_error`
    type is conservatively classified as `claude_integration_blocked` — see
    the execution plan's "위임 방식과 리스크" section for the full rationale.
    """
    if status_code in (401, 403) and error_type == "authentication_error":
        return "token_expired"
    return "claude_integration_blocked"
