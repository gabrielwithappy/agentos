from __future__ import annotations

from pathlib import Path

from agentos.llm.redaction import redact_text
from agentos.llm.tools.list import SKIPPED_DIRS
from agentos.llm.tools.paths import resolve_within_cwd
from agentos.llm.tools.types import ToolExecutionResult

GLOB_TOOL_NAME = "glob"

MAX_MATCHES = 300


def glob_tool_schema() -> dict:
    return {
        "name": GLOB_TOOL_NAME,
        "description": "Find files by name pattern (e.g. '**/*.py') inside the working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py'."},
                "path": {
                    "type": "string",
                    "description": "Directory to search from, relative to cwd. Defaults to cwd.",
                },
            },
            "required": ["pattern"],
        },
    }


def _is_skipped(candidate: Path, root: Path, blocked_roots: tuple[Path, ...]) -> bool:
    if any(part in SKIPPED_DIRS for part in candidate.relative_to(root).parts):
        return True
    return any(candidate.resolve().is_relative_to(blocked.resolve()) for blocked in blocked_roots)


def execute_glob(
    pattern: str,
    path: str = "",
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    if not pattern:
        return ToolExecutionResult(content="Error: pattern is required.", is_error=True)

    root = resolve_within_cwd(path or ".", cwd, allowed_paths, blocked_roots)
    if root is None:
        return ToolExecutionResult(
            content=f"Error: path '{path}' is outside the working directory.", is_error=True
        )
    if not root.is_dir():
        return ToolExecutionResult(content=f"Error: not a directory: {path}", is_error=True)

    matches: list[str] = []
    truncated = False
    try:
        candidates = sorted(root.glob(pattern))
    except (NotImplementedError, ValueError) as exc:
        return ToolExecutionResult(content=f"Error: invalid pattern '{pattern}': {exc}", is_error=True)

    for candidate in candidates:
        # A glob can still walk out of `root` via a symlinked directory, so
        # every hit goes back through the shared boundary.
        if resolve_within_cwd(str(candidate), cwd, allowed_paths, blocked_roots) is None:
            continue
        if _is_skipped(candidate, root, blocked_roots):
            continue
        if len(matches) >= MAX_MATCHES:
            truncated = True
            break
        matches.append(str(candidate.relative_to(cwd.resolve())))

    body = "\n".join(matches) if matches else "(no matches)"
    if truncated:
        body += f"\n[truncated: more than {MAX_MATCHES} matches]"
    return ToolExecutionResult(content=redact_text(body), truncated=truncated)


__all__ = ["GLOB_TOOL_NAME", "execute_glob", "glob_tool_schema"]
