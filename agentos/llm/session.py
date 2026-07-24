from __future__ import annotations

from collections.abc import Iterator

from agentos.llm.registry import (
    UnknownProviderError,
    UnsupportedCapabilityError,
    create_provider,
    stream_context as registry_stream_context,
    supported_providers,
)
from agentos.llm.redaction import redact_text
from agentos.llm.types import InvocationRequest, LLMEvent

SUPPORTED_PROVIDERS = set(supported_providers())


class UnsupportedProviderError(ValueError):
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Provider {provider!r} is not supported.")


def get_provider(provider: str):
    try:
        return create_provider(provider)
    except UnknownProviderError as exc:
        raise UnsupportedProviderError(redact_text(exc.provider)) from exc


def unsupported_provider_event(provider: str) -> LLMEvent:
    sanitized_provider = redact_text(provider)
    supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
    return LLMEvent(
        type="error",
        provider=sanitized_provider,
        mode="unsupported",
        error={
            "code": "unsupported_provider",
            "message": (
                f"Provider {sanitized_provider!r} is not available. "
                f"This build supports: {supported}."
            ),
        },
        recovery=f"Use one of: {supported}.",
    )


def stream_once(prompt: str, provider: str = "mock") -> Iterator[LLMEvent]:
    """Stateless compatibility shim: invokes a provider with a bare prompt
    and no prior-turn context. Legacy path for providers that do not (or
    cannot) declare `context_aware=True`."""
    return get_provider(provider).stream_once(prompt)


def unsupported_capability_event(provider: str) -> LLMEvent:
    sanitized_provider = redact_text(provider)
    return LLMEvent(
        type="error",
        provider=sanitized_provider,
        mode="unsupported-capability",
        error={
            "code": "unsupported_capability",
            "message": (
                f"Provider {sanitized_provider!r} does not support context-aware "
                "invocation and cannot resume this conversation with prior-turn context."
            ),
        },
        recovery=f"Use `agentos run --once --provider {sanitized_provider}` for a single-turn request without context.",
    )


def stream_context(request: InvocationRequest, provider: str = "mock") -> Iterator[LLMEvent]:
    """Context-aware invocation: raises no exception to callers. If the
    provider does not declare `context_aware=True`, yields a single
    sanitized `unsupported_capability_event` instead of raising, so
    callers get an explicit fallback action rather than a stack trace
    that might carry unsanitized provider internals."""
    provider_instance = get_provider(provider)
    try:
        yield from registry_stream_context(provider_instance, request)
    except UnsupportedCapabilityError:
        yield unsupported_capability_event(provider_instance.name)
