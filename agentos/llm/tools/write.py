from __future__ import annotations

from pathlib import Path

from agentos.llm.tools.paths import resolve_within_cwd
from agentos.llm.tools.types import ToolExecutionResult

WRITE_TOOL_NAME = "write"


def write_tool_schema() -> dict:
    return {
        "name": WRITE_TOOL_NAME,
        "description": "Create or overwrite a file inside the session's working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to cwd."},
                "content": {"type": "string", "description": "Full file content to write."},
            },
            "required": ["path", "content"],
        },
    }


def _resolve_writable(
    path: str,
    cwd: Path,
    allowed_paths: tuple[Path, ...],
    blocked_roots: tuple[Path, ...],
) -> Path | None:
    """`resolve_within_cwd` alone is not enough for writes: the target file
    usually does not exist yet, and a non-existent path under a symlinked
    parent would resolve somewhere unexpected. The parent directory is
    checked too, since that is what actually has to be inside `cwd`."""
    resolved = resolve_within_cwd(path, cwd, allowed_paths, blocked_roots)
    if resolved is None:
        return None
    if resolve_within_cwd(str(resolved.parent), cwd, allowed_paths, blocked_roots) is None:
        return None
    return resolved


def execute_write(
    path: str,
    content: str,
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    if not path:
        return ToolExecutionResult(content="Error: path is required.", is_error=True)

    resolved = _resolve_writable(path, cwd, allowed_paths, blocked_roots)
    if resolved is None:
        return ToolExecutionResult(
            content=f"Error: path '{path}' is outside the working directory.", is_error=True
        )
    if resolved.is_dir():
        return ToolExecutionResult(content=f"Error: path is a directory: {path}", is_error=True)
    if not resolved.parent.is_dir():
        return ToolExecutionResult(
            content=f"Error: parent directory does not exist: {path}", is_error=True
        )

    existed = resolved.is_file()
    try:
        resolved.write_text(content, encoding="utf-8")
    except OSError as exc:
        return ToolExecutionResult(content=f"Error: could not write {path}: {exc}", is_error=True)

    action = "Overwrote" if existed else "Created"
    written = len(content.encode("utf-8"))
    # Deliberately reports size only — echoing the content back would spend
    # the turn's budget re-sending what the model just produced.
    return ToolExecutionResult(content=f"{action} {path} ({written} bytes).")


__all__ = ["WRITE_TOOL_NAME", "execute_write", "write_tool_schema"]
