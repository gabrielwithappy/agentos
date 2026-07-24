from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from agentos.llm.redaction import sanitize
from agentos.llm.types import EventType, LLMEvent


RecordPolicy = Literal["none", "metadata", "full"]
TransportHint = Literal["external_cli", "direct_provider", "runtime_warm"]


@dataclass(frozen=True)
class RuntimeRequest:
    prompt: str
    provider: str = "mock"
    session_id: str | None = None
    transport_hint: TransportHint = "direct_provider"
    record_policy: RecordPolicy = "metadata"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "transport_hint": self.transport_hint,
            "record_policy": self.record_policy,
            "prompt_chars": len(self.prompt),
        }
        if self.session_id is not None:
            payload["session_id"] = self.session_id
        return sanitize(payload)


@dataclass(frozen=True)
class RuntimeTimings:
    bootstrap_ms: float
    provider_ms: float
    persistence_ms: float = 0.0
    first_event_ms: float | None = None
    total_ms: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "bootstrap_ms": round(self.bootstrap_ms, 3),
            "provider_ms": round(self.provider_ms, 3),
            "persistence_ms": round(self.persistence_ms, 3),
            "first_event_ms": None if self.first_event_ms is None else round(self.first_event_ms, 3),
            "total_ms": None if self.total_ms is None else round(self.total_ms, 3),
        }


@dataclass(frozen=True)
class InvocationEvent:
    type: EventType
    provider: str
    mode: str
    request: RuntimeRequest
    timings: RuntimeTimings
    text: str | None = None
    usage: dict[str, int] | None = None
    error: dict[str, str] | None = None
    recovery: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_llm_event(
        cls,
        event: LLMEvent,
        *,
        request: RuntimeRequest,
        timings: RuntimeTimings,
        metadata: dict[str, Any] | None = None,
    ) -> "InvocationEvent":
        merged_metadata = dict(event.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return cls(
            type=event.type,
            provider=event.provider,
            mode=event.mode,
            text=event.text,
            usage=event.usage,
            error=event.error,
            recovery=event.recovery,
            metadata=merged_metadata,
            request=request,
            timings=timings,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "provider": self.provider,
            "mode": self.mode,
            "request": self.request.to_dict(),
            "timings": self.timings.to_dict(),
        }
        if self.text is not None:
            payload["text"] = self.text
        if self.usage is not None:
            payload["usage"] = self.usage
        if self.error is not None:
            payload["error"] = self.error
        if self.recovery is not None:
            payload["recovery"] = self.recovery
        if self.metadata:
            payload["metadata"] = self.metadata
        return sanitize(payload)
