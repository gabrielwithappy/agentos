from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True)
class TransportRequest:
    """Normalized transport-level request for a single Codex Responses call.

    `messages` are already role-ordered by the caller. `previous_response_id`
    is an opaque provider continuation handle; it is never logged or
    rendered raw by transport code.
    """

    model: str
    messages: list[dict[str, Any]]
    instructions: str | None = None
    previous_response_id: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid4()))

    def to_request_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "store": True,
            "stream": True,
            "input": self.messages,
        }
        if self.instructions:
            body["instructions"] = self.instructions
        if self.previous_response_id:
            body["previous_response_id"] = self.previous_response_id
        return body


@dataclass(frozen=True)
class ProviderEvent:
    """Normalized transport-level event, distinct from `agentos.llm.types.LLMEvent`.

    `type` matches the same vocabulary the provider layer maps to
    `LLMEvent.type`: start/message_delta/reasoning/tool_call/tool_result/done/error.
    """

    type: str
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    response_id: str | None = None
    usage: dict[str, int] | None = None
    error: dict[str, str] | None = None


class TransportError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class TransportProtocol(Protocol):
    def stream(self, request: TransportRequest) -> Iterator[ProviderEvent]: ...
