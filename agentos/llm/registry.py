from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Protocol, runtime_checkable

from agentos.llm.types import InvocationRequest, LLMEvent, ProviderCapabilities, ProviderStatus


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    mode: str

    def status(self) -> ProviderStatus: ...

    def login(self) -> ProviderStatus: ...

    def logout(self) -> ProviderStatus: ...

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]: ...


def provider_capabilities(provider: LLMProvider) -> ProviderCapabilities:
    """Resolve a provider's explicit capability declaration.

    Providers without a `capabilities()` method are treated as
    `context_aware=False`: only the stateless `stream_once(prompt)` shim is
    safe to assume, matching pre-existing providers that predate the
    request-context invocation protocol.
    """
    capabilities = getattr(provider, "capabilities", None)
    if callable(capabilities):
        return capabilities()
    return ProviderCapabilities(context_aware=False)


def stream_context(provider: LLMProvider, request: InvocationRequest) -> Iterator[LLMEvent]:
    """Invoke a context-aware provider's `stream_context()`.

    Raises `UnsupportedCapabilityError` if the provider does not declare
    `context_aware=True`; callers must not silently fall back to
    `stream_once(prompt)` and drop context, since that would resend a
    multi-turn conversation as if it were the provider's first turn.
    """
    if not provider_capabilities(provider).context_aware:
        raise UnsupportedCapabilityError(provider.name)
    return provider.stream_context(request)  # type: ignore[attr-defined]


class UnsupportedCapabilityError(ValueError):
    def __init__(self, provider: str):
        super().__init__(f"Provider {provider!r} does not support context-aware invocation.")
        self.provider = provider


ProviderFactory = Callable[[], LLMProvider]


class ProviderRegistryError(ValueError):
    pass


class DuplicateProviderError(ProviderRegistryError):
    def __init__(self, provider: str):
        super().__init__(f"Provider {provider!r} is already registered.")
        self.provider = provider


class UnknownProviderError(ProviderRegistryError):
    def __init__(self, provider: str):
        super().__init__(f"Provider {provider!r} is not registered.")
        self.provider = provider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderFactory] = {}

    def register(self, provider: str, factory: ProviderFactory) -> None:
        normalized = provider.strip().lower()
        if normalized in self._providers:
            raise DuplicateProviderError(normalized)
        self._providers[normalized] = factory

    def create(self, provider: str) -> LLMProvider:
        normalized = provider.strip().lower()
        try:
            factory = self._providers[normalized]
        except KeyError as exc:
            raise UnknownProviderError(normalized) from exc
        instance = factory()
        if not isinstance(instance, LLMProvider):
            raise TypeError(f"Registered provider {normalized!r} does not satisfy LLMProvider protocol.")
        return instance

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))


def build_default_registry() -> ProviderRegistry:
    from agentos.llm.providers.codex_cli import CodexCliProvider
    from agentos.llm.providers.codex_native import CodexNativeProvider
    from agentos.llm.providers.mock import MockProvider

    registry = ProviderRegistry()
    registry.register("codex", CodexNativeProvider)
    registry.register("codex-cli", CodexCliProvider)
    registry.register("mock", MockProvider)
    return registry


_DEFAULT_REGISTRY = build_default_registry()


def default_registry() -> ProviderRegistry:
    return _DEFAULT_REGISTRY


def create_provider(provider: str) -> LLMProvider:
    return default_registry().create(provider)


def supported_providers() -> tuple[str, ...]:
    return default_registry().names()
