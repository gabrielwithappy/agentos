from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from agentos.llm.redaction import sanitize
from agentos.runtime.protocol import RecordPolicy

RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled", "interrupted"]
TerminalStatus = Literal["succeeded", "failed", "cancelled", "interrupted"]

TERMINAL_STATUSES: set[str] = {"succeeded", "failed", "cancelled", "interrupted"}
RUN_STATUSES: set[str] = {"queued", "running", *TERMINAL_STATUSES}
GATEWAY_SCHEMA_VERSION = 1


class GatewayError(ValueError):
    def __init__(self, message: str, *, code: str = "gateway_error", exit_code: int = 1):
        self.code = code
        self.exit_code = exit_code
        super().__init__(message)


class GatewayUsageError(GatewayError):
    def __init__(self, message: str, *, code: str = "usage_error"):
        super().__init__(message, code=code, exit_code=2)


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    lineage_id: str
    attempt: int
    idempotency_key: str
    status: RunStatus
    provider: str
    cwd: str
    prompt: str | None
    prompt_chars: int
    record_policy: RecordPolicy
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None
    last_error: str | None = None

    def to_dict(self, *, include_prompt: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": self.run_id,
            "lineage_id": self.lineage_id,
            "attempt": self.attempt,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "provider": self.provider,
            "cwd": self.cwd,
            "prompt_chars": self.prompt_chars,
            "record_policy": self.record_policy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.started_at:
            payload["started_at"] = self.started_at
        if self.completed_at:
            payload["completed_at"] = self.completed_at
        if self.last_error:
            payload["last_error"] = self.last_error
        if include_prompt and self.prompt is not None:
            payload["prompt"] = self.prompt
        return sanitize(payload)


@dataclass(frozen=True)
class GatewayEvent:
    run_id: str
    seq: int
    type: str
    created_at: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return sanitize(
            {
                "run_id": self.run_id,
                "seq": self.seq,
                "type": self.type,
                "created_at": self.created_at,
                "payload": self.payload,
            }
        )


def canonical_project_root(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.exists() or not candidate.is_dir() or candidate.is_symlink():
        raise GatewayUsageError(
            "Gateway cwd must be an existing regular directory. Next: choose a project directory.",
            code="invalid_cwd",
        )
    current = candidate.resolve()
    for probe in (current, *current.parents):
        if (probe / ".git").exists() or ((probe / ".agentos").is_dir() and not (probe / ".agentos").is_symlink()):
            resolved = probe.resolve()
            if any(part.is_symlink() for part in [resolved, *resolved.parents]):
                raise GatewayUsageError(
                    "Gateway project root must not include a symlink component.",
                    code="symlink_project_root",
                )
            return resolved
    raise GatewayUsageError(
        "Gateway requires a .git checkout or agentos project init marker. Next: run agentos project init --path .",
        code="project_root_missing",
    )
