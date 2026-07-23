from __future__ import annotations

from collections.abc import Iterator

from agentos.llm.registry import UnknownProviderError, create_provider, supported_providers
from agentos.llm.redaction import redact_text
from agentos.llm.types import LLMEvent

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
    return get_provider(provider).stream_once(prompt)
