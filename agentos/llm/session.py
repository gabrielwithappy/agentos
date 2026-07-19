from __future__ import annotations

from collections.abc import Iterator

from agentos.llm.providers.codex_cli import CodexCliProvider
from agentos.llm.providers.mock import MockProvider
from agentos.llm.redaction import redact_text
from agentos.llm.types import LLMEvent


SUPPORTED_PROVIDERS = {"codex", "mock"}


class UnsupportedProviderError(ValueError):
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Provider {provider!r} is not supported.")


def get_provider(provider: str) -> CodexCliProvider | MockProvider:
    normalized = provider.strip().lower()
    if normalized == "mock":
        return MockProvider()
    if normalized == "codex":
        return CodexCliProvider()
    raise UnsupportedProviderError(redact_text(provider))


def unsupported_provider_event(provider: str) -> LLMEvent:
    sanitized_provider = redact_text(provider)
    return LLMEvent(
        type="error",
        provider=sanitized_provider,
        mode="unsupported",
        error={
            "code": "unsupported_provider",
            "message": (
                f"Provider {sanitized_provider!r} is not available. "
                "This build supports the mock and codex providers."
            ),
        },
        recovery="Use --provider mock or --provider codex.",
    )


def stream_once(prompt: str, provider: str = "mock") -> Iterator[LLMEvent]:
    return get_provider(provider).stream_once(prompt)
