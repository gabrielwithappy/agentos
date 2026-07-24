from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from agentos.llm.auth import openai_codex as auth
from agentos.llm.auth.store import AuthFileStore
from agentos.llm.redaction import redact_text, sanitize
from agentos.llm.transports.base import ProviderEvent, TransportError, TransportRequest
from agentos.llm.transports.openai_codex_responses import CodexNativeTransport
from agentos.llm.types import LLMEvent, ProviderStatus

DEFAULT_MODEL = "gpt-5-codex"
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
            lambda token: CodexNativeTransport(access_token_provider=lambda: token)
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
        try:
            tokens = auth.run_browser_login()
        except auth.BrowserLaunchFailedError:
            tokens = self._device_code_login()
        except auth.AuthError as exc:
            return self._login_failed_status(exc)

        auth.persist_tokens(tokens, store=self._store)
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=True,
            authenticated=True,
            persistent_credential=True,
            status="authenticated",
            message="Codex sign-in completed.",
        )

    def login_updates(self) -> Iterator[dict[str, Any]]:
        """Same login lifecycle as `login()`, emitting a hint before the
        browser attempt so CLI/TUI callers show progress."""
        yield {"type": "hint", "text": "Complete sign-in in the browser, then return here."}
        yield {"type": "result", "payload": self.login().to_dict()}

    def _device_code_login(self):
        device_code = auth.request_device_code()
        return auth.poll_device_code(device_code)

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

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]:
        """Stateless compatibility shim: wraps `prompt` as a single-message
        request with no continuation. The canonical multi-turn path is the
        request-context invocation protocol added in a later task."""
        resolved = auth.resolve_status(self._store)
        if not resolved.authenticated:
            yield self._error_event(
                code="unauthenticated",
                message="AgentOS-owned Codex sign-in is required.",
                recovery=RECOVERY_LOGIN,
                retryable=False,
            )
            return

        record = self._store.get(auth.AUTH_PROVIDER_NAME)
        access_token = record.secrets.get("access_token") if record else None
        if not access_token:
            yield self._error_event(
                code="unauthenticated",
                message="AgentOS-owned Codex sign-in is required.",
                recovery=RECOVERY_LOGIN,
                retryable=False,
            )
            return

        transport = self._transport_factory(access_token)
        request = TransportRequest(
            model=self._model,
            messages=[{"role": "user", "content": redact_text(prompt)}],
        )

        started = False
        output_chars = 0
        try:
            for event in transport.stream(request):
                if event.type == "start":
                    started = True
                if event.type == "message_delta" and event.text:
                    output_chars += len(event.text)
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
        return LLMEvent(
            type=event.type,
            provider=self.name,
            mode=self.mode,
            text=event.text,
            usage=event.usage,
            error=sanitize(event.error) if event.error else None,
            metadata=sanitize(event.metadata) if event.metadata else {},
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
