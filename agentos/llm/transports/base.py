from __future__ import annotations

import json
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
    tools: list[dict[str, Any]] | None = None

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
        if self.tools:
            body["tools"] = [
                {
                    "type": "function",
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                }
                for tool in self.tools
            ]
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
    def __init__(
        self, code: str, message: str, *, retryable: bool = False, metadata: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.metadata = dict(metadata or {})


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
    messages: list[dict[str, Any]] = []
    for message in invocation_request.messages:
        if message.role == "system":
            continue
        if message.role != "tool":
            messages.append({"role": message.role, "content": redact_text(message.text)})
            continue
        call_id = message.metadata.get("call_id")
        name = message.metadata.get("name")
        arguments = message.metadata.get("arguments")
        if not isinstance(call_id, str) or not isinstance(name, str) or not isinstance(arguments, str):
            # Old persisted sessions have tool text but no correlation data.
            # Sending it as a generic role=tool record is not a valid Responses
            # input and inventing an output would attach it to the wrong call.
            continue
        messages.extend(
            [
                {"type": "function_call", "call_id": call_id, "name": name, "arguments": arguments},
                {"type": "function_call_output", "call_id": call_id, "output": redact_text(message.text)},
            ]
        )
    kwargs: dict[str, Any] = {}
    if session_id is not None:
        kwargs["session_id"] = session_id
    if invocation_request.tools:
        kwargs["tools"] = invocation_request.tools
    return TransportRequest(
        model=model,
        messages=messages,
        instructions=instructions,
        previous_response_id=invocation_request.continuation,
        **kwargs,
    )


def build_claude_transport_request(
    *, model: str, invocation_request: InvocationRequest, session_id: str | None = None
) -> TransportRequest:
    """Maps a provider-independent `InvocationRequest` to a Claude Messages
    `TransportRequest`.

    `system`-role messages become `instructions` (mapped to the Messages API
    top-level `system` parameter by the Claude transport — Messages has no
    `system` message role, unlike Codex Responses this is the same shape).
    Every other message keeps its caller-decided order. Unlike Codex
    Responses, Claude Messages has no top-level `function_call`/
    `function_call_output` item types: a tool call and its result are
    represented as content blocks inside ordinary `assistant`/`user`
    messages. A `role="tool"` message with complete call metadata becomes
    an `assistant` message carrying a `tool_use` content block followed by a
    `user` message carrying the matching `tool_result` content block —
    Claude requires this call/result pairing to appear in that exact
    message-role order. `invocation_request.continuation` is intentionally
    ignored: Claude Messages has no server-side conversation-continuation
    concept, so every turn always replays the full `messages` history (see
    `ProviderCapabilities.supports_continuation=False` on the Claude
    provider).
    """
    instructions_parts = [redact_text(m.text) for m in invocation_request.messages if m.role == "system"]
    instructions = "\n\n".join(instructions_parts) if instructions_parts else None
    messages: list[dict[str, Any]] = []
    for message in invocation_request.messages:
        if message.role == "system":
            continue
        if message.role != "tool":
            messages.append(
                {"role": message.role, "content": [{"type": "text", "text": redact_text(message.text)}]}
            )
            continue
        call_id = message.metadata.get("call_id")
        name = message.metadata.get("name")
        arguments = message.metadata.get("arguments")
        if not isinstance(call_id, str) or not isinstance(name, str) or not isinstance(arguments, str):
            # Old persisted sessions have tool text but no correlation data;
            # see build_transport_request() above for the same fail-closed
            # rationale (inventing a call/result pair would misattribute it).
            continue
        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError:
            parsed_arguments = {}
        messages.append(
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": call_id, "name": name, "input": parsed_arguments}
                ],
            }
        )
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": call_id, "content": redact_text(message.text)}
                ],
            }
        )
    kwargs: dict[str, Any] = {}
    if session_id is not None:
        kwargs["session_id"] = session_id
    if invocation_request.tools:
        kwargs["tools"] = invocation_request.tools
    return TransportRequest(
        model=model,
        messages=messages,
        instructions=instructions,
        previous_response_id=None,
        **kwargs,
    )
