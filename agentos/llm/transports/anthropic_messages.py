from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any, Protocol

from agentos.llm.auth.anthropic_claude import classify_auth_failure
from agentos.llm.redaction import redact_text
from agentos.llm.transports.base import ProviderEvent, TransportError, TransportRequest

DEFAULT_CLAUDE_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_CLI_VERSION_STRING = "1.0.0"
ANTHROPIC_VERSION = "2023-06-01"


def _env_base_url() -> str:
    return os.environ.get("AGENTOS_CLAUDE_BASE_URL", DEFAULT_CLAUDE_MESSAGES_URL)


def _tools_to_claude_schema(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Maps AgentOS's OpenAI-style tool schema (`name`/`description`/
    `parameters`) to Claude Messages' `name`/`description`/`input_schema`.
    Tool definitions themselves stay provider-neutral in
    `agentos/llm/tools/registry.py`; only this thin key rename is
    Claude-specific."""
    return [
        {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": tool.get("parameters", {"type": "object", "properties": {}}),
        }
        for tool in tools
    ]


def _build_request_body(request: TransportRequest) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": 8192,
        "stream": True,
    }
    if request.instructions:
        body["system"] = request.instructions
    if request.tools:
        body["tools"] = _tools_to_claude_schema(request.tools)
    return body


class SseHttpClient(Protocol):
    """Transport-level HTTP client for the SSE stream.

    Real usage streams from `urllib.request`; tests inject a fake client so
    no network access is required for unit coverage.
    """

    def stream_lines(self, url: str, *, headers: dict[str, str], body: dict[str, Any]) -> Iterator[str]: ...


class UrllibSseHttpClient:
    def stream_lines(self, url: str, *, headers: dict[str, str], body: dict[str, Any]) -> Iterator[str]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                for raw_line in response:
                    yield raw_line.decode("utf-8", errors="replace").rstrip("\n")
        except urllib.error.HTTPError as exc:
            detail = redact_text(exc.read().decode("utf-8", errors="replace"))[:500]
            raise TransportError(
                "sse_http_error",
                f"Streaming request failed (HTTP {exc.code}): {detail}",
                retryable=exc.code in (429, 500, 502, 503, 504),
            ) from exc
        except urllib.error.URLError as exc:
            raise TransportError(
                "sse_connection_failed", f"Streaming connection failed: {exc.reason}", retryable=True
            ) from exc


def _parse_sse_event(lines: list[str]) -> dict[str, Any] | None:
    data_lines = [line[len("data:") :].lstrip() for line in lines if line.startswith("data:")]
    if not data_lines:
        return None
    joined = "\n".join(data_lines)
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return None


def _iter_sse_frames(lines: Iterator[str]) -> Iterator[dict[str, Any]]:
    buffer: list[str] = []
    for line in lines:
        if line == "":
            if buffer:
                parsed = _parse_sse_event(buffer)
                buffer = []
                if parsed is not None:
                    yield parsed
            continue
        buffer.append(line)
    if buffer:
        parsed = _parse_sse_event(buffer)
        if parsed is not None:
            yield parsed


class _BlockState:
    """Per-content-block-index accumulator for one Claude Messages stream.

    Claude interleaves `content_block_start`/`content_block_delta`/
    `content_block_stop` events across multiple indices (a text block and a
    tool_use block may both be in progress at once). This state lives only
    inside a single `stream()` call; it never crosses `ProviderEvent`'s
    shared, provider-agnostic dataclass boundary.
    """

    def __init__(self) -> None:
        self.block_type: dict[int, str] = {}
        self.tool_id: dict[int, str] = {}
        self.tool_name: dict[int, str] = {}
        self.tool_json_buffer: dict[int, str] = {}
        self.usage: dict[str, int] | None = None


def map_claude_frame(frame: dict[str, Any], state: _BlockState) -> ProviderEvent | None:
    """Map one Claude Messages SSE frame to a normalized `ProviderEvent`.

    Recognized frame `type` values follow the documented Claude Messages
    streaming event vocabulary (`message_start`, `content_block_start`,
    `content_block_delta`, `content_block_stop`, `message_delta`,
    `message_stop`, `error`). Unrecognized frame types are dropped rather
    than raised, so unknown provider additions do not crash the stream.
    """
    frame_type = frame.get("type")

    if frame_type == "message_start":
        return ProviderEvent(type="start", metadata={"transport": "claude-messages"})

    if frame_type == "content_block_start":
        index = frame.get("index")
        content_block = frame.get("content_block") or {}
        block_type = content_block.get("type")
        if not isinstance(index, int):
            return None
        state.block_type[index] = block_type
        if block_type == "tool_use":
            state.tool_id[index] = content_block.get("id", "")
            state.tool_name[index] = content_block.get("name", "")
            state.tool_json_buffer[index] = ""
        return None

    if frame_type == "content_block_delta":
        index = frame.get("index")
        delta = frame.get("delta") or {}
        delta_type = delta.get("type")
        if not isinstance(index, int):
            return None
        if delta_type == "text_delta":
            text = delta.get("text")
            return ProviderEvent(type="message_delta", text=redact_text(str(text)) if text is not None else None)
        if delta_type == "input_json_delta":
            partial = delta.get("partial_json", "")
            state.tool_json_buffer[index] = state.tool_json_buffer.get(index, "") + partial
            return None
        return None

    if frame_type == "content_block_stop":
        index = frame.get("index")
        if not isinstance(index, int):
            return None
        if state.block_type.get(index) == "tool_use":
            raw_arguments = state.tool_json_buffer.get(index, "")
            try:
                arguments = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError:
                arguments = {}
            return ProviderEvent(
                type="tool_call",
                metadata={
                    "name": state.tool_name.get(index),
                    "arguments": arguments,
                    "call_id": state.tool_id.get(index),
                },
            )
        return None

    if frame_type == "message_delta":
        raw_usage = frame.get("usage")
        if isinstance(raw_usage, dict):
            state.usage = {
                "input_tokens": int(raw_usage.get("input_tokens", 0)),
                "output_tokens": int(raw_usage.get("output_tokens", 0)),
            }
        return None

    if frame_type == "message_stop":
        return ProviderEvent(type="done", usage=state.usage)

    if frame_type == "error":
        raw_error = frame.get("error") or {}
        error_type = raw_error.get("type")
        message = redact_text(str(raw_error.get("message", "Claude Messages transport reported an error.")))
        code = classify_auth_failure(error_type, 401)
        return ProviderEvent(type="error", error={"code": code, "message": message})

    return None


class ClaudeMessagesTransport:
    """SSE-only native transport for Claude Messages (OAuth Bearer auth
    with Claude-Code-impersonation headers — see the execution plan's
    "위임 방식과 리스크" section). Claude Messages has no WebSocket variant,
    unlike Codex, so this transport is intentionally simpler than
    `CodexNativeTransport`: no websocket_client/force_sse parameters."""

    def __init__(
        self,
        *,
        access_token_provider,
        base_url: str | None = None,
        sse_client: SseHttpClient | None = None,
    ):
        self._access_token_provider = access_token_provider
        self._base_url = base_url
        self._sse_client = sse_client or UrllibSseHttpClient()

    def _headers(self) -> dict[str, str]:
        token = self._access_token_provider()
        return {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "accept": "text/event-stream",
            "anthropic-beta": "claude-code-20250219,oauth-2025-04-20",
            "anthropic-version": ANTHROPIC_VERSION,
            "user-agent": f"claude-cli/{CLAUDE_CLI_VERSION_STRING}",
            "x-app": "cli",
        }

    def stream(self, request: TransportRequest) -> Iterator[ProviderEvent]:
        body = _build_request_body(request)
        url = self._base_url or _env_base_url()
        frames_source = self._sse_client.stream_lines(url, headers=self._headers(), body=body)

        state = _BlockState()
        for frame in _iter_sse_frames(frames_source):
            event = map_claude_frame(frame, state)
            if event is not None:
                yield event
