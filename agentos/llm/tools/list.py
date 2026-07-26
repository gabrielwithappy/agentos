from __future__ import annotations

from pathlib import Path

from agentos.llm.redaction import redact_text
from agentos.llm.tools.paths import resolve_within_cwd
from agentos.llm.tools.types import ToolExecutionResult

LIST_TOOL_NAME = "list"

MAX_ENTRIES = 500

# Never worth listing back to a model, and noisy enough to crowd out the
# entries that matter.
SKIPPED_DIRS = {".git", "__pycache__", ".venv", "node_modules"}


def list_tool_schema() -> dict:
    return {
        "name": LIST_TOOL_NAME,
        "description": "List the entries of a directory inside the session's working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to cwd. Defaults to cwd itself.",
                },
            },
        },
    }


def execute_list(
    path: str = "",
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    resolved = resolve_within_cwd(path or ".", cwd, allowed_paths, blocked_roots)
    if resolved is None:
        return ToolExecutionResult(
            content=f"Error: path '{path}' is outside the working directory.", is_error=True
        )
    if not resolved.is_dir():
        return ToolExecutionResult(content=f"Error: not a directory: {path}", is_error=True)

    lines: list[str] = []
    truncated = False
    for entry in sorted(resolved.iterdir(), key=lambda item: (not item.is_dir(), item.name)):
        if entry.name in SKIPPED_DIRS:
            continue
        if any(entry.resolve().is_relative_to(root.resolve()) for root in blocked_roots):
            continue
        if len(lines) >= MAX_ENTRIES:
            truncated = True
            break
        lines.append(f"{entry.name}/" if entry.is_dir() else entry.name)

    body = "\n".join(lines) if lines else "(empty)"
    if truncated:
        body += f"\n[truncated: more than {MAX_ENTRIES} entries]"
    return ToolExecutionResult(content=redact_text(body), truncated=truncated)


__all__ = ["LIST_TOOL_NAME", "execute_list", "list_tool_schema"]
