from __future__ import annotations

from pathlib import Path

from agentos.llm.tools.paths import resolve_within_cwd
from agentos.llm.tools.types import ToolExecutionResult

EDIT_TOOL_NAME = "edit"


def edit_tool_schema() -> dict:
    return {
        "name": EDIT_TOOL_NAME,
        "description": (
            "Replace an exact string in a file. `old_string` must match exactly once, "
            "so include enough surrounding context to make it unique."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to cwd."},
                "old_string": {"type": "string", "description": "Exact text to replace."},
                "new_string": {"type": "string", "description": "Replacement text."},
            },
            "required": ["path", "old_string", "new_string"],
        },
    }


def execute_edit(
    path: str,
    old_string: str,
    new_string: str,
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    if not path:
        return ToolExecutionResult(content="Error: path is required.", is_error=True)
    if not old_string:
        return ToolExecutionResult(content="Error: old_string is required.", is_error=True)

    resolved = resolve_within_cwd(path, cwd, allowed_paths, blocked_roots)
    if resolved is None:
        return ToolExecutionResult(
            content=f"Error: path '{path}' is outside the working directory.", is_error=True
        )
    if not resolved.is_file():
        return ToolExecutionResult(content=f"Error: file not found: {path}", is_error=True)

    try:
        content = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ToolExecutionResult(content=f"Error: could not read {path}: {exc}", is_error=True)

    # Requiring exactly one match is the whole safety property here: a
    # silent replace-all can rewrite far more of the file than the model
    # (or the user who approved it) intended.
    occurrences = content.count(old_string)
    if occurrences == 0:
        return ToolExecutionResult(content=f"Error: old_string not found in {path}.", is_error=True)
    if occurrences > 1:
        return ToolExecutionResult(
            content=(
                f"Error: old_string matches {occurrences} times in {path}; "
                "include more surrounding context so it is unique."
            ),
            is_error=True,
        )

    updated = content.replace(old_string, new_string)
    try:
        resolved.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return ToolExecutionResult(content=f"Error: could not write {path}: {exc}", is_error=True)

    delta = len(updated.encode("utf-8")) - len(content.encode("utf-8"))
    return ToolExecutionResult(content=f"Edited {path} ({delta:+d} bytes).")


__all__ = ["EDIT_TOOL_NAME", "execute_edit", "edit_tool_schema"]
