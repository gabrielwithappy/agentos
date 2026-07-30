from __future__ import annotations

from pathlib import Path

from agentos.conversation.threat_patterns import scan_for_threats
from agentos.llm.redaction import redact_text
from agentos.llm.tools.paths import resolve_within_cwd
from agentos.llm.tools.types import ToolExecutionResult

# Matches pi's `truncate.ts` defaults (`DEFAULT_MAX_LINES`/`DEFAULT_MAX_BYTES`).
MAX_LINES = 2000
MAX_BYTES = 50 * 1024

READ_TOOL_NAME = "read"


def read_tool_schema() -> dict:
    return {
        "name": READ_TOOL_NAME,
        "description": "Read a file from the local filesystem, relative to the session's working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path, relative to cwd or absolute within cwd."},
                "offset": {"type": "integer", "description": "0-based line number to start reading from."},
                "limit": {"type": "integer", "description": "Maximum number of lines to read."},
            },
            "required": ["path"],
        },
    }


def _truncate_lines(content: str) -> tuple[str, bool]:
    lines = content.splitlines(keepends=True)
    truncated = False
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        truncated = True
    result = "".join(lines)
    encoded = result.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        result = encoded[:MAX_BYTES].decode("utf-8", errors="ignore")
        truncated = True
    return result, truncated


def _sanitize(content: str, path: Path) -> ToolExecutionResult:
    findings = scan_for_threats(content, scope="context")
    if findings:
        blocked_text = (
            f"[BLOCKED: {path.name} contained potential prompt injection "
            f"({', '.join(findings)}). Content not loaded.]"
        )
        return ToolExecutionResult(content=blocked_text, blocked=True)

    truncated_content, truncated = _truncate_lines(content)
    sanitized = redact_text(truncated_content)
    return ToolExecutionResult(content=sanitized, truncated=truncated)


def execute_read(
    path: str,
    offset: int | None = None,
    limit: int | None = None,
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    resolved = resolve_within_cwd(path, cwd, allowed_paths, blocked_roots)
    if resolved is None:
        return ToolExecutionResult(content=f"Error: path '{path}' is outside the working directory.", is_error=True)

    if not resolved.is_file():
        return ToolExecutionResult(content=f"Error: file not found: {path}", is_error=True)

    try:
        content = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return ToolExecutionResult(content=f"Error: could not read {path}: {exc}", is_error=True)
    except UnicodeDecodeError as exc:
        return ToolExecutionResult(content=f"Error: could not decode {path}: {exc}", is_error=True)

    if offset is not None or limit is not None:
        # Providers occasionally serialize integer-typed tool arguments as
        # strings (e.g. `{"limit": "60"}`); coerce defensively so `start +
        # limit` below never raises TypeError on a str operand.
        lines = content.splitlines(keepends=True)
        start = int(offset) if offset is not None else 0
        end = start + int(limit) if limit is not None else None
        content = "".join(lines[start:end])

    return _sanitize(content, resolved)
