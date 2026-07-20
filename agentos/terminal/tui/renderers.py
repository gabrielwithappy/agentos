from __future__ import annotations

from typing import Any

from agentos.llm.redaction import sanitize


def render_event(event: dict[str, Any]) -> str:
    safe = sanitize(event)
    event_type = str(safe.get("type", "event"))
    if event_type == "message_delta":
        return str(safe.get("text", ""))
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
