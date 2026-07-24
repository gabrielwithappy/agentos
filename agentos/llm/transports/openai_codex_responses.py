from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any, Protocol

from agentos.llm.redaction import redact_text
from agentos.llm.transports.base import ProviderEvent, TransportError, TransportRequest

DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api"


def _env_base_url() -> str:
    return os.environ.get("AGENTOS_CODEX_BASE_URL", DEFAULT_CODEX_BASE_URL)


def resolve_responses_url(base_url: str | None = None) -> str:
    raw = base_url or _env_base_url()
    normalized = raw.rstrip("/")
    if normalized.endswith("/codex/responses"):
        return normalized
    if normalized.endswith("/codex"):
        return f"{normalized}/responses"
    return f"{normalized}/codex/responses"


def resolve_websocket_url(base_url: str | None = None) -> str:
    url = resolve_responses_url(base_url)
    if url.startswith("https:"):
        return "wss:" + url[len("https:") :]
    if url.startswith("http:"):
        return "ws:" + url[len("http:") :]
    return url


class SseHttpClient(Protocol):
    """Transport-level HTTP client for the SSE fallback path.

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
        except urllib.error.URLError as exc:
            raise TransportError("sse_connection_failed", "Streaming connection failed.", retryable=True) from exc


class WebSocketClient(Protocol):
    """Minimal WebSocket transport used when a WebSocket implementation is
    available. Tests inject a fake client; production resolves an optional
    `websockets`-compatible implementation, falling back to SSE when absent."""

    def send_and_stream(self, url: str, *, headers: dict[str, str], body: dict[str, Any]) -> Iterator[str]: ...


def _resolve_websocket_client() -> WebSocketClient | None:
    """Returns a WebSocket client only if a WebSocket implementation is
    importable. AgentOS does not require `websockets` as a hard dependency;
    its absence is a normal, automatic SSE fallback, not an error."""
    try:
        import websockets  # noqa: F401
    except ImportError:
        return None
    return None  # A full WebSocket client wiring is added when the optional dependency is present.


def _parse_sse_event(lines: list[str]) -> dict[str, Any] | None:
    data_lines = [line[len("data:") :].lstrip() for line in lines if line.startswith("data:")]
    if not data_lines:
        return None
    joined = "\n".join(data_lines)
    if joined == "[DONE]":
        return None
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


def map_codex_frame(frame: dict[str, Any]) -> ProviderEvent | None:
    """Map one Codex Responses stream frame to a normalized `ProviderEvent`.

    Recognized frame `type` values follow the documented Responses stream
    event vocabulary (`response.created`, `response.output_text.delta`,
    `response.reasoning_summary_text.delta`, function/tool call events,
    `response.completed`, `response.failed`, `error`). Unrecognized frame
    types are dropped rather than raised, so unknown provider additions do
    not crash the stream.
    """
    frame_type = frame.get("type")
    response_id = None
    response_obj = frame.get("response")
    if isinstance(response_obj, dict):
        response_id = response_obj.get("id")

    if frame_type == "response.created":
        return ProviderEvent(type="start", response_id=response_id, metadata={"transport": "codex-native"})
    if frame_type in ("response.output_text.delta", "response.output_text_delta"):
        delta = frame.get("delta")
        text = redact_text(str(delta)) if delta is not None else None
        return ProviderEvent(type="message_delta", text=text, response_id=response_id)
    if frame_type in ("response.reasoning_summary_text.delta", "response.reasoning_text.delta"):
        delta = frame.get("delta")
        text = redact_text(str(delta)) if delta is not None else None
        return ProviderEvent(type="reasoning", text=text, response_id=response_id)
    if frame_type in ("response.function_call_arguments.delta", "response.output_item.added"):
        item = frame.get("item")
        if isinstance(item, dict) and item.get("type") in ("function_call", "custom_tool_call"):
            return ProviderEvent(
                type="tool_call",
                metadata={"name": item.get("name"), "arguments": item.get("arguments")},
                response_id=response_id,
            )
        return None
    if frame_type == "response.output_item.done":
        item = frame.get("item")
        if isinstance(item, dict) and item.get("type") in (
            "function_call_output",
            "custom_tool_call_output",
        ):
            summary = item.get("output") or item.get("result")
            return ProviderEvent(
                type="tool_result",
                metadata={"summary": redact_text(str(summary)) if summary else ""},
                response_id=response_id,
            )
        return None
    if frame_type == "response.completed":
        usage = None
        if isinstance(response_obj, dict) and isinstance(response_obj.get("usage"), dict):
            raw_usage = response_obj["usage"]
            usage = {
                "input_tokens": int(raw_usage.get("input_tokens", 0)),
                "output_tokens": int(raw_usage.get("output_tokens", 0)),
            }
        return ProviderEvent(type="done", response_id=response_id, usage=usage)
    if frame_type in ("response.failed", "error"):
        raw_error = frame.get("error") or frame.get("response", {}).get("error") or {}
        message = redact_text(str(raw_error.get("message", "Codex native transport reported an error.")))
        code = str(raw_error.get("code", "codex_native_error"))
        return ProviderEvent(type="error", response_id=response_id, error={"code": code, "message": message})
    return None


class CodexNativeTransport:
    """WebSocket-first, SSE-fallback native transport for Codex Responses.

    Selection is automatic and silent to callers: `websocket_client`
    (injectable for tests) is tried first; when no WebSocket implementation
    is available the transport uses SSE without raising, since the
    optional WebSocket dependency is not required for AgentOS to function.
    """

    def __init__(
        self,
        *,
        access_token_provider,
        base_url: str | None = None,
        sse_client: SseHttpClient | None = None,
        websocket_client: WebSocketClient | None = None,
        force_sse: bool = False,
    ):
        self._access_token_provider = access_token_provider
        self._base_url = base_url
        self._sse_client = sse_client or UrllibSseHttpClient()
        self._websocket_client = websocket_client if not force_sse else None
        self._force_sse = force_sse

    def _headers(self) -> dict[str, str]:
        token = self._access_token_provider()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
        }

    def stream(self, request: TransportRequest) -> Iterator[ProviderEvent]:
        body = request.to_request_body()
        client = self._websocket_client if not self._force_sse else None
        if client is not None:
            frames_source = client.send_and_stream(
                resolve_websocket_url(self._base_url), headers=self._headers(), body=body
            )
        else:
            frames_source = self._sse_client.stream_lines(
                resolve_responses_url(self._base_url), headers=self._headers(), body=body
            )

        for frame in _iter_sse_frames(frames_source) if client is None else _iter_websocket_frames(frames_source):
            event = map_codex_frame(frame)
            if event is not None:
                yield event


def _iter_websocket_frames(lines: Iterator[str]) -> Iterator[dict[str, Any]]:
    for line in lines:
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue
