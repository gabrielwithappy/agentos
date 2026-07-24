from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Protocol

from agentos.llm.auth.store import AuthFileStore
from agentos.llm.auth.types import AuthRecord
from agentos.llm.redaction import redact_text

DEFAULT_ISSUER = "https://auth.openai.com"
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CALLBACK_PORT = 1455
FALLBACK_CALLBACK_PORT = 1457
DEVICE_CODE_MAX_WAIT_SECONDS = 15 * 60
AUTH_PROVIDER_NAME = "codex"
CREDENTIAL_TYPE = "account-login"
_REFRESH_LOCK = threading.Lock()


def _env_issuer() -> str:
    return os.environ.get("AGENTOS_CODEX_ISSUER", DEFAULT_ISSUER)


def _env_client_id() -> str:
    return os.environ.get("AGENTOS_CODEX_CLIENT_ID", CLIENT_ID)


class HttpTransport(Protocol):
    """Minimal HTTP transport used by login/device-code/refresh flows.

    Real usage goes through `urllib.request`; tests inject a fake transport
    so no network access is required for unit coverage.
    """

    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def open_browser(self, url: str) -> bool: ...


class UrllibHttpTransport:
    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
        return json.loads(raw)

    def open_browser(self, url: str) -> bool:
        import webbrowser

        try:
            return webbrowser.open(url)
        except Exception:
            return False


@dataclass(frozen=True)
class PkceCodes:
    code_verifier: str
    code_challenge: str


def generate_pkce() -> PkceCodes:
    verifier_bytes = secrets.token_bytes(64)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PkceCodes(code_verifier=code_verifier, code_challenge=code_challenge)


def generate_state() -> str:
    return secrets.token_urlsafe(32)


class AuthError(Exception):
    """Sanitized auth-flow error. Message never contains raw secrets."""

    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class StateMismatchError(AuthError):
    def __init__(self) -> None:
        super().__init__("state_mismatch", "Login callback state did not match. Please try again.")


class BrowserLaunchFailedError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            "browser_launch_failed",
            "Could not open a browser for sign-in.",
            retryable=True,
        )


class CallbackTimeoutError(AuthError):
    def __init__(self) -> None:
        super().__init__("callback_timeout", "Sign-in did not complete in time.", retryable=True)


class DeviceCodeExpiredError(AuthError):
    def __init__(self) -> None:
        super().__init__("device_code_expired", "The device sign-in code expired.", retryable=True)


class DeviceCodeCancelledError(AuthError):
    def __init__(self) -> None:
        super().__init__("device_code_cancelled", "Device sign-in was cancelled.")


@dataclass(frozen=True)
class TokenResult:
    id_token: str
    access_token: str
    refresh_token: str
    account_label: str | None = None
    expires_in: float | None = None


def _find_free_port(preferred: int, fallback: int) -> int:
    for candidate in (preferred, fallback):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", candidate))
                return candidate
        except OSError:
            continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def build_authorize_url(*, issuer: str, client_id: str, redirect_uri: str, state: str, pkce: PkceCodes) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email offline_access",
        "state": state,
        "code_challenge": pkce.code_challenge,
        "code_challenge_method": "S256",
    }
    query = urllib.parse.urlencode(params)
    return f"{issuer.rstrip('/')}/oauth/authorize?{query}"


class _CallbackResult:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.code: str | None = None
        self.state: str | None = None
        self.error: str | None = None


def _make_callback_handler(expected_state: str, result: _CallbackResult) -> type[BaseHTTPRequestHandler]:
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/auth/callback":
                self.send_response(404)
                self.end_headers()
                return
            query = urllib.parse.parse_qs(parsed.query)
            state = query.get("state", [None])[0]
            code = query.get("code", [None])[0]
            error = query.get("error", [None])[0]

            if error:
                result.error = redact_text(error)
            elif state != expected_state:
                result.error = "state_mismatch"
            else:
                result.code = code
                result.state = state

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            body = (
                "<html><body>Sign-in complete. You can close this window.</body></html>"
                if not result.error
                else "<html><body>Sign-in failed. Return to the terminal.</body></html>"
            )
            self.wfile.write(body.encode("utf-8"))
            result.event.set()

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    return CallbackHandler


def run_browser_login(
    *,
    transport: HttpTransport | None = None,
    issuer: str | None = None,
    client_id: str | None = None,
    timeout_seconds: float = 300.0,
    open_browser: bool = True,
) -> TokenResult:
    """Browser-callback login: opens a local HTTP server, launches the
    browser to the authorize URL, waits for the redirect, then exchanges the
    authorization code for tokens. Raises `AuthError` subclasses on failure;
    never returns or logs a raw authorization code, token, or callback query.
    """
    resolved_issuer = issuer or _env_issuer()
    resolved_client_id = client_id or _env_client_id()
    http = transport or UrllibHttpTransport()

    port = _find_free_port(DEFAULT_CALLBACK_PORT, FALLBACK_CALLBACK_PORT)
    redirect_uri = f"http://localhost:{port}/auth/callback"
    pkce = generate_pkce()
    state = generate_state()

    result = _CallbackResult()
    handler_cls = _make_callback_handler(state, result)
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    auth_url = build_authorize_url(
        issuer=resolved_issuer,
        client_id=resolved_client_id,
        redirect_uri=redirect_uri,
        state=state,
        pkce=pkce,
    )

    if open_browser:
        opened = http.open_browser(auth_url)
        if not opened:
            server.server_close()
            raise BrowserLaunchFailedError()

    completed = result.event.wait(timeout=timeout_seconds)
    server.server_close()

    if not completed:
        raise CallbackTimeoutError()
    if result.error == "state_mismatch":
        raise StateMismatchError()
    if result.error:
        raise AuthError("callback_error", "Sign-in failed during the browser callback.")
    if not result.code:
        raise AuthError("callback_missing_code", "Sign-in callback did not include an authorization code.")

    return _exchange_code_for_tokens(
        http,
        issuer=resolved_issuer,
        client_id=resolved_client_id,
        redirect_uri=redirect_uri,
        pkce=pkce,
        authorization_code=result.code,
    )


def _exchange_code_for_tokens(
    http: HttpTransport,
    *,
    issuer: str,
    client_id: str,
    redirect_uri: str,
    pkce: PkceCodes,
    authorization_code: str,
) -> TokenResult:
    token_endpoint = f"{issuer.rstrip('/')}/oauth/token"
    try:
        payload = http.post_json(
            token_endpoint,
            {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code": authorization_code,
                "code_verifier": pkce.code_verifier,
            },
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise AuthError("token_exchange_failed", "Token exchange failed.", retryable=True) from exc
    return _token_result_from_payload(payload)


def _token_result_from_payload(payload: dict[str, Any]) -> TokenResult:
    try:
        return TokenResult(
            id_token=str(payload["id_token"]),
            access_token=str(payload["access_token"]),
            refresh_token=str(payload["refresh_token"]),
            account_label=str(payload["account_label"]) if payload.get("account_label") else None,
            expires_in=float(payload["expires_in"]) if payload.get("expires_in") is not None else None,
        )
    except KeyError as exc:
        raise AuthError("token_response_invalid", "Sign-in response was missing required fields.") from exc


@dataclass(frozen=True)
class DeviceCode:
    verification_url: str
    user_code: str
    device_auth_id: str
    interval: float


def request_device_code(
    *,
    transport: HttpTransport | None = None,
    issuer: str | None = None,
    client_id: str | None = None,
) -> DeviceCode:
    resolved_issuer = (issuer or _env_issuer()).rstrip("/")
    resolved_client_id = client_id or _env_client_id()
    http = transport or UrllibHttpTransport()

    try:
        payload = http.post_json(
            f"{resolved_issuer}/api/accounts/deviceauth/usercode",
            {"client_id": resolved_client_id},
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise AuthError("device_code_request_failed", "Could not start device sign-in.", retryable=True) from exc

    try:
        return DeviceCode(
            verification_url=f"{resolved_issuer}/codex/device",
            user_code=str(payload["user_code"]),
            device_auth_id=str(payload["device_auth_id"]),
            interval=float(payload.get("interval", 5)),
        )
    except KeyError as exc:
        raise AuthError("device_code_response_invalid", "Device sign-in response was invalid.") from exc


def poll_device_code(
    device_code: DeviceCode,
    *,
    transport: HttpTransport | None = None,
    issuer: str | None = None,
    client_id: str | None = None,
    max_wait_seconds: float = DEVICE_CODE_MAX_WAIT_SECONDS,
    cancel_event: threading.Event | None = None,
    sleep: Any = time.sleep,
) -> TokenResult:
    """Poll the device-code token endpoint until success, expiry, or cancel.

    Uses the server-provided `interval` as the backoff between polls and
    honors HTTP 403/404 as "pending" per the documented device-auth
    contract. `cancel_event` allows cooperative cancellation from the CLI.
    """
    resolved_issuer = (issuer or _env_issuer()).rstrip("/")
    resolved_client_id = client_id or _env_client_id()
    http = transport or UrllibHttpTransport()

    deadline = time.monotonic() + max_wait_seconds
    url = f"{resolved_issuer}/api/accounts/deviceauth/token"

    while True:
        if cancel_event is not None and cancel_event.is_set():
            raise DeviceCodeCancelledError()
        if time.monotonic() >= deadline:
            raise DeviceCodeExpiredError()

        try:
            payload = http.post_json(
                url,
                {
                    "device_auth_id": device_code.device_auth_id,
                    "user_code": device_code.user_code,
                },
            )
        except _PendingAuthorization:
            sleep(device_code.interval)
            continue
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise AuthError("device_code_poll_failed", "Device sign-in polling failed.", retryable=True) from exc

        pkce = PkceCodes(
            code_verifier=str(payload["code_verifier"]),
            code_challenge=str(payload["code_challenge"]),
        )
        redirect_uri = f"{resolved_issuer}/deviceauth/callback"
        return _exchange_code_for_tokens(
            http,
            issuer=resolved_issuer,
            client_id=resolved_client_id,
            redirect_uri=redirect_uri,
            pkce=pkce,
            authorization_code=str(payload["authorization_code"]),
        )


class _PendingAuthorization(Exception):
    """Raised by test transports to signal HTTP 403/404 pending status."""


def _expiry_timestamp(expires_in: float | None) -> float | None:
    if expires_in is None:
        return None
    return time.time() + expires_in


def persist_tokens(
    tokens: TokenResult,
    *,
    store: AuthFileStore,
) -> AuthRecord:
    """Persist native Codex tokens to the local auth store.

    Only `store`-managed secrets carry token values; callers must not log
    or render `tokens` directly.
    """
    record = AuthRecord(
        provider=AUTH_PROVIDER_NAME,
        credential_type=CREDENTIAL_TYPE,
        authenticated=True,
        secrets={
            "id_token": tokens.id_token,
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
        },
        account_label=tokens.account_label,
        metadata={"expires_at": _expiry_timestamp(tokens.expires_in)},
    )
    return store.upsert(record)


def refresh_access_token(
    refresh_token: str,
    *,
    transport: HttpTransport | None = None,
    issuer: str | None = None,
    client_id: str | None = None,
) -> TokenResult:
    """Exchange a stored refresh token for a fresh access token.

    Callers must hold `_REFRESH_LOCK`-equivalent discipline; this function
    itself serializes concurrent refreshes for the same process via
    `_REFRESH_LOCK` to avoid redundant network calls racing each other.
    """
    resolved_issuer = (issuer or _env_issuer()).rstrip("/")
    resolved_client_id = client_id or _env_client_id()
    http = transport or UrllibHttpTransport()

    with _REFRESH_LOCK:
        try:
            payload = http.post_json(
                f"{resolved_issuer}/oauth/token",
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
    issuer: str | None = None,
    client_id: str | None = None,
    now: float | None = None,
) -> ResolvedStatus:
    """Resolve current auth status, refreshing an expired access token
    transparently when a refresh token is available. Never returns or logs
    a raw token value.
    """
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
            issuer=issuer,
            client_id=client_id,
        )
    except AuthError:
        return ResolvedStatus(authenticated=False, status="expired")

    persist_tokens(refreshed_tokens, store=store)
    return ResolvedStatus(
        authenticated=True,
        status="authenticated",
        account_label=refreshed_tokens.account_label or record.account_label,
        refreshed=True,
    )


def logout(store: AuthFileStore) -> bool:
    """Delete the local native Codex auth record. Idempotent: returns True
    only when a record was actually removed; a repeated logout is still a
    sanitized success from the caller's perspective."""
    return store.delete(AUTH_PROVIDER_NAME)
