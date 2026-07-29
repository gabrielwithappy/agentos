from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from agentos.llm.auth import anthropic_claude as auth
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.redaction import redact_text, sanitize
from agentos.llm.transports.anthropic_messages import ClaudeMessagesTransport
from agentos.llm.transports.base import (
    ProviderEvent,
    TransportError,
    TransportRequest,
    build_claude_transport_request,
)
from agentos.llm.types import InvocationRequest, LLMEvent, ProviderCapabilities, ProviderStatus

DEFAULT_MODEL = "claude-sonnet-5"
NATIVE_MODE = "account-login"
RECOVERY_LOGIN = "Run: agentos llm login --provider claude"
RECOVERY_INTEGRATION_BLOCKED = (
    "This is a documented policy risk, not a bug you caused. Check for an AgentOS update if re-login does not resolve it."
)


class ClaudeNativeProvider:
    """Canonical `claude` provider: AgentOS-owned native OAuth auth/transport
    for Claude Pro/Max subscriptions, mirroring `CodexNativeProvider`'s
    structure. Unlike `codex`, there is no `claude-cli` delegation sibling
    and no device-code login fallback (Anthropic does not publicly offer
    one) — a failed browser launch surfaces directly to the caller."""

    name = "claude"
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
            lambda token: ClaudeMessagesTransport(access_token_provider=lambda: token)
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
                message="AgentOS-owned Claude sign-in is required.",
                recovery=RECOVERY_LOGIN,
                next_command="agentos llm login --provider claude",
            )
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=True,
            authenticated=True,
            persistent_credential=True,
            status="authenticated",
            message="Signed in with Claude account-login.",
        )

    def login(self) -> ProviderStatus:
        status: ProviderStatus | None = None
        for kind, value in self._login_steps():
            if kind == "status":
                status = value
        assert status is not None  # _login_steps() always yields exactly one "status"
        return status

    def login_updates(self) -> Iterator[dict[str, Any]]:
        """Same login lifecycle as `login()`, but streams a `hint` for the
        browser sign-in URL as soon as it is known — shown regardless of
        whether auto-launch succeeds, since the caller has no way to know
        that in advance."""
        for kind, value in self._login_steps():
            if kind == "hint":
                yield {"type": "hint", "text": value}
            else:
                yield {"type": "result", "payload": value.to_dict()}

    def _login_steps(self) -> Iterator[tuple[str, Any]]:
        """Shared implementation for `login()` and `login_updates()`. Yields
        `("hint", text)` tuples as progress becomes known, and exactly one
        `("status", ProviderStatus)` as the final item.

        There is no device-code fallback here (unlike Codex): Anthropic does
        not publicly offer one, so a failed browser launch ends the attempt
        directly rather than trying a second flow."""
        try:
            prepared = auth.prepare_browser_login()
        except auth.AuthError as exc:
            # e.g. the fixed local callback port is already in use — there is
            # no URL to hint at yet, so this fails straight to a status.
            yield ("status", self._login_failed_status(exc))
            return
        yield ("hint", f"Open this URL to sign in:\n{prepared.auth_url}")
        try:
            tokens = auth.complete_browser_login(prepared)
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
                message="Claude sign-in completed.",
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
            message="Claude sign-in did not complete successfully.",
            recovery=RECOVERY_LOGIN,
            next_command="agentos llm login --provider claude",
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
                "Claude sign-out completed."
                if removed
                else "Claude was already signed out."
            ),
        )

    def capabilities(self) -> ProviderCapabilities:
        # Claude Messages has no server-side continuation handle: every turn
        # replays the full message history, unlike Codex's
        # `previous_response_id`.
        return ProviderCapabilities(context_aware=True, supports_continuation=False)

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]:
        """Stateless compatibility shim: wraps `prompt` as a single-message
        request with no continuation. The canonical multi-turn path is
        `stream_context()`."""
        access_token = self._authenticated_access_token()
        if access_token is None:
            yield self._unauthenticated_event()
            return

        transport_request = TransportRequest(
            model=self._model,
            messages=[{"role": "user", "content": [{"type": "text", "text": redact_text(prompt)}]}],
        )
        yield from self._stream_via_transport(access_token, transport_request)

    def stream_context(self, request: InvocationRequest) -> Iterator[LLMEvent]:
        """Canonical multi-turn path: sends the caller-ordered conversation
        context to the transport. `request.continuation` is intentionally
        ignored by `build_claude_transport_request()` — see that function's
        docstring and `capabilities().supports_continuation=False`."""
        access_token = self._authenticated_access_token()
        if access_token is None:
            yield self._unauthenticated_event()
            return

        transport_request = build_claude_transport_request(model=self._model, invocation_request=request)
        yield from self._stream_via_transport(access_token, transport_request)

    def _authenticated_access_token(self) -> str | None:
        resolved = auth.resolve_status(self._store)
        if not resolved.authenticated:
            return None
        record = self._store.get(auth.AUTH_PROVIDER_NAME)
        if record is None:
            return None
        return record.secrets.get("access_token")

    def _unauthenticated_event(self) -> LLMEvent:
        return self._error_event(
            code="unauthenticated",
            message="AgentOS-owned Claude sign-in is required.",
            recovery=RECOVERY_LOGIN,
            retryable=False,
        )

    def _stream_via_transport(self, access_token: str, transport_request: TransportRequest) -> Iterator[LLMEvent]:
        transport = self._transport_factory(access_token)

        started = False
        try:
            for event in transport.stream(transport_request):
                if event.type == "start":
                    started = True
                yield self._to_llm_event(event)
        except TransportError as exc:
            if not started:
                yield LLMEvent(type="start", provider=self.name, mode=self.mode, metadata={"transport": "claude-messages"})
            yield self._error_event(
                code=exc.code,
                message=redact_text(exc.message),
                recovery="Resend your message.",
                retryable=exc.retryable,
            )

    def _to_llm_event(self, event: ProviderEvent) -> LLMEvent:
        metadata = dict(event.metadata) if event.metadata else {}
        if event.type == "error" and event.error is not None:
            code = event.error.get("code")
            message = event.error.get("message", "")
            if code == "claude_integration_blocked":
                return self._error_event(
                    code=code,
                    message=(
                        "Claude 로그인 연동이 Anthropic 정책 변경으로 차단되었을 수 있습니다(알려진 리스크). "
                        "재로그인으로 해결되지 않으면 AgentOS 업데이트를 확인하세요."
                    ),
                    recovery=RECOVERY_INTEGRATION_BLOCKED,
                    retryable=False,
                )
            return self._error_event(
                code="token_expired",
                message="Claude 로그인이 만료되었습니다. 다시 로그인하세요.",
                recovery=RECOVERY_LOGIN,
                retryable=False,
            )
        return LLMEvent(
            type=event.type,
            provider=self.name,
            mode=self.mode,
            text=redact_text(event.text) if event.text is not None else None,
            usage=event.usage,
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
