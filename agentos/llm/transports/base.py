from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

from agentos.llm.redaction import redact_text
from agentos.llm.types import InvocationRequest


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
            "store": False,
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


def build_transport_request(
    *, model: str, invocation_request: InvocationRequest, session_id: str | None = None
) -> TransportRequest:
    """Maps a provider-independent `InvocationRequest` to a Codex Responses
    `TransportRequest`.

    `system`-role messages become `instructions` (Responses has no `system`
    input role); every other message keeps its caller-decided order.
    `invocation_request.continuation` becomes `previous_response_id`
    verbatim — it is an opaque handle, never inspected or logged. When
    `continuation` is absent (fresh session, expired handle, restart/resume)
    `previous_response_id` stays unset and `messages` carries the full
    replay the caller already assembled, since there is no provider-side
    history to resume from.
    """
    instructions_parts = [redact_text(m.text) for m in invocation_request.messages if m.role == "system"]
    instructions = "\n\n".join(instructions_parts) if instructions_parts else None
    messages = [
        {"role": m.role, "content": redact_text(m.text)}
        for m in invocation_request.messages
        if m.role != "system"
    ]
    kwargs: dict[str, Any] = {}
    if session_id is not None:
        kwargs["session_id"] = session_id
    return TransportRequest(
        model=model,
        messages=messages,
        instructions=instructions,
        previous_response_id=invocation_request.continuation,
        **kwargs,
    )
