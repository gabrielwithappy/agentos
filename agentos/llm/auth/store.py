from __future__ import annotations

import json
import threading
from pathlib import Path

from agentos.llm.auth.types import AuthRecord
from agentos.terminal.paths import agentos_home, atomic_write_json, ensure_contained, set_user_only_permissions


AUTH_SCHEMA_VERSION = "agentos.auth/v1"
_STORE_LOCK = threading.Lock()


class AuthFileStore:
    def __init__(self, home: str | Path | None = None, filename: str = "auth.json") -> None:
        self.root = agentos_home(home)
        self.path = ensure_contained(self.root / filename, self.root)

    def list_records(self) -> list[AuthRecord]:
        payload = self._read_payload()
        records = payload.get("records", {})
        return [AuthRecord.from_dict(value) for _, value in sorted(records.items())]

    def get(self, provider: str) -> AuthRecord | None:
        payload = self._read_payload()
        raw = payload.get("records", {}).get(provider.strip().lower())
        if raw is None:
            return None
        return AuthRecord.from_dict(raw)

    def upsert(self, record: AuthRecord) -> AuthRecord:
        normalized = record.provider.strip().lower()
        with _STORE_LOCK:
            payload = self._read_payload()
            records = dict(payload.get("records", {}))
            records[normalized] = AuthRecord(
                provider=normalized,
                credential_type=record.credential_type,
                authenticated=record.authenticated,
                secrets=record.secrets,
                account_label=record.account_label,
                metadata=record.metadata,
            ).to_dict()
            self._write_payload(records)
        return self.get(normalized) or record

    def delete(self, provider: str) -> bool:
        normalized = provider.strip().lower()
        with _STORE_LOCK:
            payload = self._read_payload()
            records = dict(payload.get("records", {}))
            removed = records.pop(normalized, None)
            self._write_payload(records)
        return removed is not None

    def _read_payload(self) -> dict:
        if not self.path.exists():
            return {"schema_version": AUTH_SCHEMA_VERSION, "records": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != AUTH_SCHEMA_VERSION:
            raise ValueError("Existing auth store has an incompatible schema.")
        return data

    def _write_payload(self, records: dict[str, dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        set_user_only_permissions(self.root, directory=True)
        atomic_write_json(
            self.path,
            {
                "schema_version": AUTH_SCHEMA_VERSION,
                "records": records,
            },
        )
