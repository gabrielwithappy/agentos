from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentos.conversation.threat_patterns import scan_for_threats
from agentos.llm.redaction import redact_text

# Matches pi's `truncate.ts` defaults (`DEFAULT_MAX_LINES`/`DEFAULT_MAX_BYTES`).
MAX_LINES = 2000
MAX_BYTES = 50 * 1024

READ_TOOL_NAME = "read"


@dataclass(frozen=True)
class ToolExecutionResult:
    """Outcome of one tool execution, ready to become a `role="tool"`
    `ConversationMessage` text. `blocked` mirrors `bootstrap.ContextFile`'s
    `skipped`/`blocked` split: a skip/error means the file couldn't be
    produced; a block means it was read fine but content matched a threat
    pattern, so `content` already holds a `[BLOCKED: ...]` marker instead of
    the raw text."""

    content: str
    is_error: bool = False
    truncated: bool = False
    blocked: bool = False


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


def _resolve_allowed_path(path: str, cwd: Path, allowed_paths: tuple[Path, ...] = ()) -> Path | None:
    """Resolves `path` against `cwd` and returns it only if the fully
    resolved path (symlinks included) lands inside `cwd`. Resolution happens
    before the containment check — checking first would let a symlink whose
    target lives outside `cwd` slip through undetected."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    resolved = candidate.resolve()
    resolved_cwd = cwd.resolve()
    if resolved.is_relative_to(resolved_cwd):
        return resolved
    resolved_allowed = tuple(candidate.resolve() for candidate in allowed_paths)
    if resolved not in resolved_allowed:
        return None
    return resolved


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
) -> ToolExecutionResult:
    resolved = _resolve_allowed_path(path, cwd, allowed_paths)
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
        lines = content.splitlines(keepends=True)
        start = offset or 0
        end = start + limit if limit is not None else None
        content = "".join(lines[start:end])

    return _sanitize(content, resolved)
