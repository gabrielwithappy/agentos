from __future__ import annotations

from pathlib import Path

from agentos.llm.tools.paths import resolve_within_cwd

# Approval summaries are deliberately NOT built with
# `renderers.format_tool_arguments` + `truncate(limit=120)`. That helper
# truncates from the head, so the tail of a command chain -- exactly where
# `&& rm -rf ...` tends to live -- is what disappears. A user must never
# approve an irreversible action whose dangerous part was cut off screen.

MAX_COMMAND_CHARS = 2000
CONTENT_PREVIEW_LINES = 5


def _elide_middle(text: str, limit: int) -> str:
    """Keeps both ends of `text` when it must be shortened, so a command's
    tail stays visible."""
    if len(text) <= limit:
        return text
    keep = (limit - 5) // 2
    return f"{text[:keep]}\n…\n{text[-keep:]}"


def describe_tool_call(name: str, arguments: dict, *, cwd: Path) -> str:
    """Human-readable description of a pending tool call, shown to the user
    before it runs. Shared by the TUI modal and the CLI prompt so the two
    front-ends can never drift into showing different amounts of detail."""
    if name == "bash":
        command = str(arguments.get("command", ""))
        lines = [
            "실행할 명령:",
            _elide_middle(command, MAX_COMMAND_CHARS) or "(빈 명령)",
            "",
            "주의: bash는 샌드박스가 아닙니다. 승인하면 작업 폴더 밖에도 영향을 줄 수 있습니다.",
        ]
        return "\n".join(lines)

    if name == "write":
        path = str(arguments.get("path", ""))
        content = str(arguments.get("content", ""))
        resolved = resolve_within_cwd(path, cwd) if path else None
        if resolved is not None and resolved.is_file():
            state = f"덮어씀 (현재 {resolved.stat().st_size} bytes)"
        else:
            state = "새로 만듦"
        body = content.splitlines()
        preview = "\n".join(body[:CONTENT_PREVIEW_LINES])
        if len(body) > CONTENT_PREVIEW_LINES:
            preview += f"\n… (총 {len(body)}줄)"
        return (
            f"파일: {path}\n"
            f"동작: {state}\n"
            f"쓸 내용: {len(content.encode('utf-8'))} bytes / {len(body)}줄\n"
            f"{preview}"
        )

    if name == "edit":
        path = str(arguments.get("path", ""))
        old = str(arguments.get("old_string", ""))
        new = str(arguments.get("new_string", ""))
        return (
            f"파일: {path}\n"
            f"바꾸기 전:\n{_elide_middle(old, MAX_COMMAND_CHARS)}\n"
            f"바꾼 후:\n{_elide_middle(new, MAX_COMMAND_CHARS)}"
        )

    details = ", ".join(f"{key}={value}" for key, value in arguments.items())
    return f"{name}({details})"


def approval_prompt(name: str, arguments: dict, *, cwd: Path, call_number: int = 1) -> str:
    """Full approval text including the per-turn call counter, which exists
    so a user facing a run of prompts can see how many they have already
    approved this turn rather than answering on reflex."""
    return (
        f"도구 실행 승인 필요 — {name} (이번 턴 {call_number}번째 도구 승인)\n"
        f"{describe_tool_call(name, arguments, cwd=cwd)}"
    )


__all__ = ["approval_prompt", "describe_tool_call"]
