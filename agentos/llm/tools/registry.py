from __future__ import annotations

from pathlib import Path
from typing import Literal

from agentos.llm.tools.read import READ_TOOL_NAME, ToolExecutionResult, execute_read, read_tool_schema

ToolName = Literal["read"]

_SCHEMAS = {READ_TOOL_NAME: read_tool_schema}


def get_tool_schemas(names: list[ToolName]) -> list[dict]:
    return [_SCHEMAS[name]() for name in names]


def execute_tool(name: str, arguments: dict, *, cwd: Path) -> ToolExecutionResult:
    if name == READ_TOOL_NAME:
        return execute_read(
            arguments.get("path", ""),
            arguments.get("offset"),
            arguments.get("limit"),
            cwd=cwd,
        )
    return ToolExecutionResult(content=f"Error: unknown tool '{name}'.", is_error=True)


__all__ = ["ToolName", "get_tool_schemas", "execute_tool"]
