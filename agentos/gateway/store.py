from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentos.gateway.types import GATEWAY_SCHEMA_VERSION, RUN_STATUSES, TERMINAL_STATUSES, GatewayError, GatewayUsageError, GatewayEvent, RunRecord, RunStatus
from agentos.llm.redaction import sanitize
from agentos.runtime.protocol import RecordPolicy
from agentos.terminal.paths import agentos_home, set_user_only_permissions


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class GatewayStore:
    def __init__(self, home: str | Path | None = None):
        self.home = agentos_home(home)
        self.root = self.home / "gateway"
        self.db_path = self.root / "gateway.db"

    def initialize(self) -> None:
        if self.root.exists() and self.root.is_symlink():
            raise GatewayError("Gateway directory must not be a symlink.", code="symlink_gateway_dir")
        self.root.mkdir(parents=True, exist_ok=True)
        set_user_only_permissions(self.root, directory=True)
        with self._connect() as conn:
            user_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if user_version > GATEWAY_SCHEMA_VERSION:
                raise GatewayError("Gateway database schema is newer than this AgentOS build.", code="unsupported_schema")
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    lineage_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    prompt TEXT,
                    prompt_chars INTEGER NOT NULL,
                    record_policy TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    last_error TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(run_id, seq),
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
                """
            )
            conn.execute(f"PRAGMA user_version={GATEWAY_SCHEMA_VERSION}")
        for path in (self.db_path, self.db_path.with_name("gateway.db-wal"), self.db_path.with_name("gateway.db-shm")):
            if path.exists():
                set_user_only_permissions(path, directory=False)

    def _connect(self) -> sqlite3.Connection:
        if self.db_path.exists() and self.db_path.is_symlink():
            raise GatewayError("Gateway database must not be a symlink.", code="symlink_gateway_db")
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.DatabaseError as exc:
            raise GatewayError("Gateway database could not be opened.", code="db_corrupt") from exc
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create_run(
        self,
        *,
        prompt: str,
        provider: str,
        cwd: str,
        record_policy: RecordPolicy = "metadata",
        idempotency_key: str | None = None,
    ) -> RunRecord:
        self.initialize()
        now = utc_now()
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        lineage_id = run_id
        key = idempotency_key or f"{cwd}:{provider}:{record_policy}:{prompt}"
        # Metadata policy keeps the prompt only until the worker reaches a
        # terminal state; transition() purges it before retention/prune.
        stored_prompt = prompt
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM runs WHERE idempotency_key=?", (key,)).fetchone()
            if existing:
                return _record(existing)
            conn.execute(
                """
                INSERT INTO runs(run_id,lineage_id,attempt,idempotency_key,status,provider,cwd,prompt,prompt_chars,record_policy,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (run_id, lineage_id, 1, key, "queued", provider, cwd, stored_prompt, len(prompt), record_policy, now, now),
            )
            conn.commit()
        self.append_event(run_id, "queued", {"provider": provider, "cwd": cwd, "record_policy": record_policy, "prompt_chars": len(prompt)})
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> RunRecord:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise GatewayUsageError(f"Unknown run {run_id}. Next: agentos gateway list", code="unknown_run")
        return _record(row)

    def list_runs(self, status: str | None = None) -> list[RunRecord]:
        self.initialize()
        with self._connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM runs WHERE status=? ORDER BY created_at, run_id", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM runs ORDER BY created_at, run_id").fetchall()
        return [_record(row) for row in rows]

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> GatewayEvent:
        now = utc_now()
        payload = sanitize(payload)
        with self._connect() as conn:
            current = conn.execute("SELECT COALESCE(MAX(seq), 0) FROM events WHERE run_id=?", (run_id,)).fetchone()[0]
            seq = int(current) + 1
            conn.execute(
                "INSERT INTO events(run_id, seq, type, created_at, payload_json) VALUES(?,?,?,?,?)",
                (run_id, seq, event_type, now, __import__("json").dumps(payload, sort_keys=True)),
            )
            conn.commit()
        return GatewayEvent(run_id=run_id, seq=seq, type=event_type, created_at=now, payload=payload)

    def events(self, run_id: str) -> list[GatewayEvent]:
        self.initialize()
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,)).fetchall()
        return [_event(row) for row in rows]

    def transition(self, run_id: str, status: RunStatus, *, last_error: str | None = None) -> RunRecord:
        if status not in RUN_STATUSES:
            raise GatewayUsageError("Invalid run status.", code="invalid_status")
        current = self.get_run(run_id)
        if current.status in TERMINAL_STATUSES:
            raise GatewayUsageError("Terminal runs cannot transition.", code="terminal_run")
        now = utc_now()
        started_at = current.started_at or (now if status == "running" else None)
        completed_at = now if status in TERMINAL_STATUSES else None
        prompt = None if status in {"succeeded", "failed", "cancelled", "interrupted"} and current.record_policy == "metadata" else current.prompt
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status=?, updated_at=?, started_at=?, completed_at=?, last_error=?, prompt=? WHERE run_id=?",
                (status, now, started_at, completed_at, last_error, prompt, run_id),
            )
            conn.commit()
        self.append_event(run_id, status, {"status": status, "error": last_error} if last_error else {"status": status})
        return self.get_run(run_id)

    def claim_next(self) -> RunRecord | None:
        self.initialize()
        now = utc_now()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM runs WHERE status='queued' ORDER BY created_at, run_id LIMIT 1").fetchone()
            if row is None:
                conn.commit()
                return None
            conn.execute(
                "UPDATE runs SET status='running', started_at=?, updated_at=? WHERE run_id=? AND status='queued'",
                (now, now, row["run_id"]),
            )
            conn.commit()
        self.append_event(row["run_id"], "running", {"status": "running"})
        return self.get_run(row["run_id"])

    def recover_orphans(self) -> int:
        self.initialize()
        now = utc_now()
        with self._connect() as conn:
            rows = conn.execute("SELECT run_id FROM runs WHERE status='running'").fetchall()
            for row in rows:
                conn.execute(
                    "UPDATE runs SET status='interrupted', updated_at=?, completed_at=?, last_error=? WHERE run_id=?",
                    (now, now, "Recovered after worker restart.", row["run_id"]),
                )
            conn.commit()
        for row in rows:
            self.append_event(row["run_id"], "interrupted", {"status": "interrupted", "error": "Recovered after worker restart."})
        return len(rows)

    def cancel(self, run_id: str) -> RunRecord:
        run = self.get_run(run_id)
        if run.status == "running":
            raise GatewayUsageError("Running runs cannot be cancelled in Gateway Core MVP.", code="running_cancel_rejected")
        if run.status in TERMINAL_STATUSES:
            raise GatewayUsageError("Terminal runs cannot be cancelled.", code="terminal_run")
        return self.transition(run_id, "cancelled")

    def retry(self, run_id: str, *, prompt: str | None, yes: bool) -> RunRecord:
        run = self.get_run(run_id)
        if run.status not in {"failed", "interrupted"}:
            raise GatewayUsageError("Only failed or interrupted runs can be retried.", code="retry_not_allowed")
        next_prompt = prompt or run.prompt
        if not next_prompt:
            raise GatewayUsageError("Metadata runs require a new prompt for retry. Next: agentos gateway retry RUN_ID \"prompt\" --yes", code="prompt_required")
        if not yes:
            raise GatewayUsageError("Retry preview only. Add --yes to create the new attempt.", code="confirmation_required")
        new_run_id = f"run_{uuid.uuid4().hex[:16]}"
        now = utc_now()
        stored_prompt = next_prompt if run.record_policy == "full" else None
        with self._connect() as conn:
            attempt = int(conn.execute("SELECT COALESCE(MAX(attempt), 0) FROM runs WHERE lineage_id=?", (run.lineage_id,)).fetchone()[0]) + 1
            conn.execute(
                """
                INSERT INTO runs(run_id,lineage_id,attempt,idempotency_key,status,provider,cwd,prompt,prompt_chars,record_policy,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (new_run_id, run.lineage_id, attempt, f"retry:{run.run_id}:{attempt}:{uuid.uuid4().hex}", "queued", run.provider, run.cwd, stored_prompt, len(next_prompt), run.record_policy, now, now),
            )
            conn.commit()
        self.append_event(new_run_id, "queued", {"retry_of": run_id, "attempt": attempt})
        return self.get_run(new_run_id)

    def prune(self, *, before: str, yes: bool) -> dict[str, Any]:
        self.initialize()
        with self._connect() as conn:
            rows = conn.execute("SELECT run_id FROM runs WHERE status IN ('succeeded','failed','cancelled','interrupted') AND updated_at < ?", (before,)).fetchall()
            run_ids = [row["run_id"] for row in rows]
            if yes and run_ids:
                conn.executemany("DELETE FROM events WHERE run_id=?", [(run_id,) for run_id in run_ids])
                conn.executemany("DELETE FROM runs WHERE run_id=?", [(run_id,) for run_id in run_ids])
                conn.commit()
        if yes and run_ids:
            with self._connect() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return {"matched": len(run_ids), "deleted": len(run_ids) if yes else 0, "run_ids": run_ids, "requires_yes": not yes}


def _record(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        run_id=row["run_id"],
        lineage_id=row["lineage_id"],
        attempt=int(row["attempt"]),
        idempotency_key=row["idempotency_key"],
        status=row["status"],
        provider=row["provider"],
        cwd=row["cwd"],
        prompt=row["prompt"],
        prompt_chars=int(row["prompt_chars"]),
        record_policy=row["record_policy"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        last_error=row["last_error"],
    )


def _event(row: sqlite3.Row) -> GatewayEvent:
    import json

    return GatewayEvent(
        run_id=row["run_id"],
        seq=int(row["seq"]),
        type=row["type"],
        created_at=row["created_at"],
        payload=json.loads(row["payload_json"]),
    )
