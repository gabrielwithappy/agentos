from __future__ import annotations

import subprocess
from pathlib import Path

from agentos.llm.redaction import redact_text
from agentos.llm.tools.paths import truncate_output
from agentos.llm.tools.types import ToolExecutionResult

BASH_TOOL_NAME = "bash"

DEFAULT_TIMEOUT_SECONDS = 120
MAX_TIMEOUT_SECONDS = 600
MAX_OUTPUT_BYTES = 30 * 1024


def bash_tool_schema() -> dict:
    return {
        "name": BASH_TOOL_NAME,
        "description": (
            "Run a shell command from the session's working directory. "
            "Requires user approval on every call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run."},
                "timeout": {
                    "type": "integer",
                    "description": f"Seconds before the command is killed (default {DEFAULT_TIMEOUT_SECONDS}).",
                },
            },
            "required": ["command"],
        },
    }


def execute_bash(
    command: str,
    timeout: int | None = None,
    *,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> ToolExecutionResult:
    """Runs `command` through a shell, pinned to `cwd`.

    This is not a sandbox. Pinning `cwd` only sets where the process
    *starts*; it does not constrain what the command may touch, so unlike
    every other tool here `bash` can reach outside the working directory.
    The real control line is the per-call user approval enforced by
    `agentos.llm.tools.registry.requires_confirmation`. `allowed_paths` and
    `blocked_roots` are accepted for a uniform call signature and
    deliberately unused.
    """
    if not command.strip():
        return ToolExecutionResult(content="Error: command is required.", is_error=True)

    resolved_timeout = DEFAULT_TIMEOUT_SECONDS if timeout is None else int(timeout)
    resolved_timeout = max(1, min(resolved_timeout, MAX_TIMEOUT_SECONDS))

    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=resolved_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # `subprocess.run` already kills the child before re-raising.
        return ToolExecutionResult(
            content=f"Error: command timed out after {resolved_timeout}s.", is_error=True
        )
    except OSError as exc:
        return ToolExecutionResult(content=f"Error: could not run command: {exc}", is_error=True)

    body = (completed.stdout or "") + (completed.stderr or "")
    body, truncated = truncate_output(body, MAX_OUTPUT_BYTES)
    if truncated:
        body += f"\n[truncated: output exceeded {MAX_OUTPUT_BYTES} bytes]"
    if not body.strip():
        body = "(no output)"

    summary = f"exit={completed.returncode}\n{body}"
    return ToolExecutionResult(
        content=redact_text(summary),
        is_error=completed.returncode != 0,
        truncated=truncated,
    )


__all__ = ["BASH_TOOL_NAME", "execute_bash", "bash_tool_schema"]
