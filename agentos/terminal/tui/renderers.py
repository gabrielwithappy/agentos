from __future__ import annotations

from typing import Any

from agentos.llm.redaction import sanitize

TRUNCATE_LIMIT = 120


def truncate(text: str, limit: int = TRUNCATE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_tool_arguments(arguments: Any) -> str:
    if isinstance(arguments, dict):
        return ", ".join(f"{key}={value}" for key, value in arguments.items())
    if isinstance(arguments, list):
        return ", ".join(str(value) for value in arguments)
    if arguments is None:
        return ""
    return str(arguments)


def format_tool_summary(name: str, arguments: Any, result_summary: str) -> str:
    args_text = truncate(format_tool_arguments(arguments))
    result_text = truncate(str(result_summary or ""))
    return f"{name}({args_text}) -> {result_text}"


def render_event(event: dict[str, Any]) -> str:
    safe = sanitize(event)
    event_type = str(safe.get("type", "event"))
    if event_type == "message_delta":
        return str(safe.get("text", ""))
    if event_type == "reasoning":
        return f"Thinking: {truncate(str(safe.get('text', '')))}"
    if event_type == "tool_call":
        metadata = safe.get("metadata") or {}
        name = metadata.get("name", "tool")
        args_summary = truncate(format_tool_arguments(metadata.get("arguments")))
        return f"Tool call: {name}({args_summary})"
    if event_type == "tool_result":
        metadata = safe.get("metadata") or {}
        return f"Tool result: {truncate(str(metadata.get('summary', '')))}"
    if event_type == "error":
        error = safe.get("error", {})
        if isinstance(error, dict):
            message = error.get("message", "Provider error.")
        else:
            message = "Provider error."
        return f"{message} Next: /status"
    if event_type == "hook_error":
        return "Hook failed. Next: /hooks"
    return event_type


def render_session_summary(row: dict[str, Any]) -> str:
    safe = sanitize(row)
    status = "unavailable" if not safe.get("available", False) else "available"
    label = f" {safe.get('label')}" if safe.get("label") else ""
    return (
        f"{safe.get('short_id', '?')} {safe.get('provider', '?')} "
        f"{safe.get('mode', '?')} {safe.get('updated_at', '')}{label} {status}"
    ).strip()
