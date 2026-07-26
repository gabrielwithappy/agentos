from __future__ import annotations

from pathlib import Path
from typing import Literal

from agentos.llm.tools.bash import BASH_TOOL_NAME, bash_tool_schema, execute_bash
from agentos.llm.tools.edit import EDIT_TOOL_NAME, edit_tool_schema, execute_edit
from agentos.llm.tools.glob import GLOB_TOOL_NAME, execute_glob, glob_tool_schema
from agentos.llm.tools.grep import GREP_TOOL_NAME, execute_grep, grep_tool_schema
from agentos.llm.tools.list import LIST_TOOL_NAME, execute_list, list_tool_schema
from agentos.llm.tools.read import READ_TOOL_NAME, execute_read, read_tool_schema
from agentos.llm.tools.types import ToolExecutionResult
from agentos.llm.tools.write import WRITE_TOOL_NAME, execute_write, write_tool_schema

ToolName = Literal["read", "list", "glob", "grep", "write", "edit", "bash"]

ALL_TOOL_NAMES: tuple[ToolName, ...] = ("read", "list", "glob", "grep", "write", "edit", "bash")

_SCHEMAS = {
    READ_TOOL_NAME: read_tool_schema,
    LIST_TOOL_NAME: list_tool_schema,
    GLOB_TOOL_NAME: glob_tool_schema,
    GREP_TOOL_NAME: grep_tool_schema,
    WRITE_TOOL_NAME: write_tool_schema,
    EDIT_TOOL_NAME: edit_tool_schema,
    BASH_TOOL_NAME: bash_tool_schema,
}

# Tools whose effects cannot be undone from inside AgentOS. These are gated
# on explicit user approval for every call, independent of any environment
# variable — see `requires_confirmation`.
_MUTATING_TOOLS = frozenset({WRITE_TOOL_NAME, EDIT_TOOL_NAME, BASH_TOOL_NAME})


def get_tool_schemas(names: list[ToolName]) -> list[dict]:
    return [_SCHEMAS[name]() for name in names]


def requires_confirmation(name: str) -> bool:
    """Whether `name` must be approved by the user before every execution.

    Read-only tools return `False` and stay opt-in via
    `AGENTOS_TOOL_READ_CONFIRM`; mutating tools return `True` and are never
    env-gated, because a default-off environment variable would otherwise
    let file writes and shell commands run unannounced.
    """
    return name in _MUTATING_TOOLS


def execute_tool(
    name: str,
    arguments: dict,
    *,
    cwd: Path,
    allowed_read_paths: tuple[Path, ...] = (),
    blocked_read_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    boundary = {
        "cwd": cwd,
        "allowed_paths": allowed_read_paths,
        "blocked_roots": blocked_read_roots,
    }
    if name == READ_TOOL_NAME:
        return execute_read(
            arguments.get("path", ""),
            arguments.get("offset"),
            arguments.get("limit"),
            **boundary,
        )
    if name == LIST_TOOL_NAME:
        return execute_list(arguments.get("path", ""), **boundary)
    if name == GLOB_TOOL_NAME:
        return execute_glob(arguments.get("pattern", ""), arguments.get("path", ""), **boundary)
    if name == GREP_TOOL_NAME:
        return execute_grep(
            arguments.get("pattern", ""),
            arguments.get("path", ""),
            arguments.get("glob", "**/*"),
            **boundary,
        )
    if name == WRITE_TOOL_NAME:
        return execute_write(arguments.get("path", ""), arguments.get("content", ""), **boundary)
    if name == EDIT_TOOL_NAME:
        return execute_edit(
            arguments.get("path", ""),
            arguments.get("old_string", ""),
            arguments.get("new_string", ""),
            **boundary,
        )
    if name == BASH_TOOL_NAME:
        return execute_bash(arguments.get("command", ""), arguments.get("timeout"), **boundary)
    return ToolExecutionResult(content=f"Error: unknown tool '{name}'.", is_error=True)


__all__ = [
    "ALL_TOOL_NAMES",
    "ToolName",
    "execute_tool",
    "get_tool_schemas",
    "requires_confirmation",
]
