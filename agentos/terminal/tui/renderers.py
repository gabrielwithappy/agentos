from __future__ import annotations

from typing import Any, Callable

from agentos.llm.redaction import sanitize

TRUNCATE_LIMIT = 120

TOOL_RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {}


def register_tool_renderer(name: str, renderer: Callable[[dict[str, Any]], str]) -> None:
    """Register a custom renderer for a `tool_result` event with the given tool name.

    The renderer receives the already-`sanitize()`d event dict (never the raw
    payload), so it must not re-fetch or bypass sanitization.
    """
    TOOL_RENDERERS[name] = renderer


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
        renderer = TOOL_RENDERERS.get(str(metadata.get("name", "")))
        if renderer is not None:
            return renderer(safe)
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


def render_turn_tree(events: list[dict[str, Any]]) -> str:
    parent_of: dict[str, str | None] = {}
    turn_order: list[str] = []
    for event in events:
        turn_id = event.get("turn_id")
        if not turn_id:
            continue
        if turn_id not in parent_of:
            parent_of[turn_id] = None
            turn_order.append(turn_id)
        candidate = event.get("parent_turn_id")
        if candidate is not None:
            parent_of[turn_id] = candidate

    if not turn_order:
        return "No turns yet. Next: send a message."

    children: dict[str | None, list[str]] = {}
    for turn_id in turn_order:
        children.setdefault(parent_of[turn_id], []).append(turn_id)

    lines: list[str] = []

    def walk(turn_id: str, prefix: str, is_last: bool) -> None:
        connector = "└─ " if is_last else "├─ "
        lines.append(f"{prefix}{connector}{turn_id[:8]}")
        next_prefix = prefix + ("   " if is_last else "│  ")
        kids = children.get(turn_id, [])
        for index, child in enumerate(kids):
            walk(child, next_prefix, index == len(kids) - 1)

    roots = children.get(None, [])
    for index, root in enumerate(roots):
        walk(root, "", index == len(roots) - 1)

    return "\n".join(lines)


def render_mock_tool_table(safe_payload: dict[str, Any]) -> str:
    """Example custom renderer: shows the mock provider's tool_result as a table.

    `safe_payload` has already been through `sanitize()` by the caller
    (`render_event`), so this renderer must not need a second sanitize pass.
    """
    metadata = safe_payload.get("metadata") or {}
    rows = [(key, value) for key, value in metadata.items() if key != "name"]
    lines = ["| field | value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {truncate(str(value))} |")
    return "\n".join(lines)


register_tool_renderer("mock_tool", render_mock_tool_table)


def render_session_summary(row: dict[str, Any]) -> str:
    safe = sanitize(row)
    status = "unavailable" if not safe.get("available", False) else "available"
    label = f" {safe.get('label')}" if safe.get("label") else ""
    return (
        f"{safe.get('short_id', '?')} {safe.get('provider', '?')} "
        f"{safe.get('mode', '?')} {safe.get('updated_at', '')}{label} {status}"
    ).strip()
