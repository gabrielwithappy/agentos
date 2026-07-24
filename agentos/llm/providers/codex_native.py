from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from agentos.llm.auth import openai_codex as auth
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.redaction import redact_text, sanitize
from agentos.llm.transports.base import (
    ProviderEvent,
    TransportError,
    TransportRequest,
    build_transport_request,
)
from agentos.llm.transports.openai_codex_responses import CodexNativeTransport
from agentos.llm.types import InvocationRequest, LLMEvent, ProviderCapabilities, ProviderStatus

DEFAULT_MODEL = "gpt-5.5"
NATIVE_MODE = "account-login"
RECOVERY_LOGIN = "Run: agentos llm login --provider codex"


class CodexNativeProvider:
    """Canonical `codex` provider: AgentOS-owned native auth/transport.

    This provider never falls back to the external CLI automatically; that
    remains a separate, explicit recovery/debug path chosen by the caller
    (`agentos/llm/providers/codex_cli.py`), not by this class.
    """

    name = "codex"
    mode = NATIVE_MODE

    def __init__(
        self,
        *,
        store: AuthFileStore | None = None,
        transport_factory=None,
        model: str = DEFAULT_MODEL,
    ):
        self._store = store or AuthFileStore()
        self._transport_factory = transport_factory or (
            lambda token, account_id: CodexNativeTransport(
                access_token_provider=lambda: token,
                account_id_provider=lambda: account_id,
            )
        )
        self._model = model

    def status(self) -> ProviderStatus:
        resolved = auth.resolve_status(self._store)
        if not resolved.authenticated:
            return ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=False,
                authenticated=False,
                persistent_credential=False,
                status=resolved.status,
                message="AgentOS-owned Codex sign-in is required.",
                recovery=RECOVERY_LOGIN,
                next_command="agentos llm login --provider codex",
            )
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=True,
            authenticated=True,
            persistent_credential=True,
            status="authenticated",
            message="Signed in with Codex account-login.",
        )

    def login(self) -> ProviderStatus:
        status: ProviderStatus | None = None
        for kind, value in self._login_steps():
            if kind == "status":
                status = value
        assert status is not None  # _login_steps() always yields exactly one "status"
        return status

    def login_updates(self) -> Iterator[dict[str, Any]]:
        """Same login lifecycle as `login()`, but streams a `hint` for every
        actionable URL/code as soon as it is known — the browser sign-in
        URL immediately (shown regardless of whether auto-launch succeeds,
        since the caller has no way to know that in advance), and the
        device-code verification URL/code if browser auto-launch fails and
        AgentOS falls back to device sign-in."""
        for kind, value in self._login_steps():
            if kind == "hint":
                yield {"type": "hint", "text": value}
            else:
                yield {"type": "result", "payload": value.to_dict()}

    def _login_steps(self) -> Iterator[tuple[str, Any]]:
        """Shared implementation for `login()` and `login_updates()`. Yields
        `("hint", text)` tuples as progress becomes known, and exactly one
        `("status", ProviderStatus)` as the final item."""
        prepared = auth.prepare_browser_login()
        yield ("hint", f"Open this URL to sign in:\n{prepared.auth_url}")
        try:
            tokens = auth.complete_browser_login(prepared)
        except auth.BrowserLaunchFailedError:
            try:
                device_code = auth.request_device_code()
            except auth.AuthError as exc:
                # The device-code fallback is itself a network call and can
                # fail independently of the browser attempt (e.g. no network
                # access to the auth issuer) — this must not propagate as an
                # unhandled exception out of a Textual worker thread.
                yield ("status", self._login_failed_status(exc))
                return
            yield (
                "hint",
                "Could not open a browser automatically.\n"
                f"Open {device_code.verification_url} and enter code: {device_code.user_code}",
            )
            try:
                tokens = auth.poll_device_code(device_code)
            except auth.AuthError as exc:
                yield ("status", self._login_failed_status(exc))
                return
        except auth.AuthError as exc:
            yield ("status", self._login_failed_status(exc))
            return

        auth.persist_tokens(tokens, store=self._store)
        yield (
            "status",
            ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=True,
                authenticated=True,
                persistent_credential=True,
                status="authenticated",
                message="Codex sign-in completed.",
            ),
        )

    def _login_failed_status(self, exc: auth.AuthError) -> ProviderStatus:
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="failed",
            message="Codex sign-in did not complete successfully.",
            recovery=RECOVERY_LOGIN,
            next_command="agentos llm login --provider codex",
        )

    def logout(self) -> ProviderStatus:
        removed = auth.logout(self._store)
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="logged_out",
            message=(
                "Codex sign-out completed."
                if removed
                else "Codex was already signed out."
            ),
        )

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(context_aware=True, supports_continuation=True)

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]:
        """Stateless compatibility shim: wraps `prompt` as a single-message
        request with no continuation. The canonical multi-turn path is
        `stream_context()`."""
        credentials = self._authenticated_credentials()
        if credentials is None:
            yield self._unauthenticated_event()
            return
        access_token, account_id = credentials

        transport_request = TransportRequest(
            model=self._model,
            messages=[{"role": "user", "content": redact_text(prompt)}],
        )
        yield from self._stream_via_transport(access_token, account_id, transport_request)

    def stream_context(self, request: InvocationRequest) -> Iterator[LLMEvent]:
        """Canonical multi-turn path: sends the caller-ordered conversation
        context plus an opaque continuation handle (if any) to the
        transport. The handle is passed through verbatim — never inspected,
        logged, or exposed raw outside `LLMEvent.metadata`."""
        credentials = self._authenticated_credentials()
        if credentials is None:
            yield self._unauthenticated_event()
            return
        access_token, account_id = credentials

        transport_request = build_transport_request(model=self._model, invocation_request=request)
        yield from self._stream_via_transport(access_token, account_id, transport_request)

    def _authenticated_credentials(self) -> tuple[str, str | None] | None:
        resolved = auth.resolve_status(self._store)
        if not resolved.authenticated:
            return None
        record = self._store.get(auth.AUTH_PROVIDER_NAME)
        if record is None:
            return None
        access_token = record.secrets.get("access_token")
        if not access_token:
            return None
        id_token = record.secrets.get("id_token")
        account_id = auth.chatgpt_account_id_from_id_token(id_token) if id_token else None
        return access_token, account_id

    def _unauthenticated_event(self) -> LLMEvent:
        return self._error_event(
            code="unauthenticated",
            message="AgentOS-owned Codex sign-in is required.",
            recovery=RECOVERY_LOGIN,
            retryable=False,
        )

    def _stream_via_transport(
        self, access_token: str, account_id: str | None, transport_request: TransportRequest
    ) -> Iterator[LLMEvent]:
        transport = self._transport_factory(access_token, account_id)

        started = False
        try:
            for event in transport.stream(transport_request):
                if event.type == "start":
                    started = True
                yield self._to_llm_event(event)
        except TransportError as exc:
            if not started:
                yield LLMEvent(type="start", provider=self.name, mode=self.mode, metadata={"transport": "codex-native"})
            yield self._error_event(
                code=exc.code,
                message=redact_text(exc.message),
                recovery="Resend your message.",
                retryable=exc.retryable,
            )

    def _to_llm_event(self, event: ProviderEvent) -> LLMEvent:
        metadata = dict(event.metadata) if event.metadata else {}
        if event.response_id:
            metadata["continuation"] = event.response_id
        return LLMEvent(
            type=event.type,
            provider=self.name,
            mode=self.mode,
            text=redact_text(event.text) if event.text is not None else None,
            usage=event.usage,
            error=sanitize(event.error) if event.error else None,
            metadata=sanitize(metadata) if metadata else {},
        )

    def _error_event(self, *, code: str, message: str, recovery: str, retryable: bool) -> LLMEvent:
        return LLMEvent(
            type="error",
            provider=self.name,
            mode=self.mode,
            error={"code": code, "message": message},
            recovery=recovery,
            metadata={"retryable": retryable},
        )
