from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Protocol, runtime_checkable

from agentos.llm.types import LLMEvent, ProviderStatus


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    mode: str

    def status(self) -> ProviderStatus: ...

    def login(self) -> ProviderStatus: ...

    def logout(self) -> ProviderStatus: ...

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]: ...


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
