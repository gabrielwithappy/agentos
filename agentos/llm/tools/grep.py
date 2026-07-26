from __future__ import annotations

import re
from pathlib import Path

from agentos.llm.redaction import redact_text
from agentos.llm.tools.list import SKIPPED_DIRS
from agentos.llm.tools.paths import resolve_within_cwd, truncate_output
from agentos.llm.tools.types import ToolExecutionResult

GREP_TOOL_NAME = "grep"

MAX_MATCHES = 200
MAX_BYTES = 50 * 1024
# Files larger than this are almost certainly build output or binaries; a
# content search that reads them wastes the turn's budget.
MAX_FILE_BYTES = 2 * 1024 * 1024


def grep_tool_schema() -> dict:
    return {
        "name": GREP_TOOL_NAME,
        "description": "Search file contents by regular expression inside the working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Python regular expression."},
                "path": {
                    "type": "string",
                    "description": "Directory to search from, relative to cwd. Defaults to cwd.",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional filename filter, e.g. '**/*.py'. Defaults to all files.",
                },
            },
            "required": ["pattern"],
        },
    }


def execute_grep(
    pattern: str,
    path: str = "",
    glob: str = "**/*",
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    if not pattern:
        return ToolExecutionResult(content="Error: pattern is required.", is_error=True)

    # A bad regex is a normal outcome of a model guessing a pattern, so it
    # comes back as a tool error the model can correct, never an exception.
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return ToolExecutionResult(content=f"Error: invalid regex '{pattern}': {exc}", is_error=True)

    root = resolve_within_cwd(path or ".", cwd, allowed_paths, blocked_roots)
    if root is None:
        return ToolExecutionResult(
            content=f"Error: path '{path}' is outside the working directory.", is_error=True
        )
    if not root.is_dir():
        return ToolExecutionResult(content=f"Error: not a directory: {path}", is_error=True)

    lines: list[str] = []
    truncated = False
    for candidate in sorted(root.glob(glob or "**/*")):
        if not candidate.is_file():
            continue
        if any(part in SKIPPED_DIRS for part in candidate.relative_to(root).parts):
            continue
        if resolve_within_cwd(str(candidate), cwd, allowed_paths, blocked_roots) is None:
            continue
        try:
            if candidate.stat().st_size > MAX_FILE_BYTES:
                continue
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        relative = candidate.relative_to(cwd.resolve())
        for number, line in enumerate(content.splitlines(), start=1):
            if not compiled.search(line):
                continue
            if len(lines) >= MAX_MATCHES:
                truncated = True
                break
            lines.append(f"{relative}:{number}:{line.strip()}")
        if truncated:
            break

    body = "\n".join(lines) if lines else "(no matches)"
    body, byte_truncated = truncate_output(body, MAX_BYTES)
    truncated = truncated or byte_truncated
    if truncated:
        body += "\n[truncated: too many matches]"
    return ToolExecutionResult(content=redact_text(body), truncated=truncated)


__all__ = ["GREP_TOOL_NAME", "execute_grep", "grep_tool_schema"]
