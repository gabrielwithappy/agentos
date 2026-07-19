from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from agentos.terminal.events import CLI_EVENT_SCHEMA_VERSION
from agentos.terminal.paths import agentos_home, atomic_write_json, atomic_write_text, set_user_only_permissions

SESSION_SCHEMA_VERSION = "agentos.session/v1"


class SessionError(ValueError):
    pass


def validate_session_id(session_id: str) -> str:
    try:
        parsed = UUID(session_id)
    except ValueError as exc:
        raise SessionError(f"Session {session_id} was not found. Next: agentos session list") from exc
    return str(parsed)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sessions_dir(home: str | Path | None = None) -> Path:
    path = agentos_home(home) / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    set_user_only_permissions(path, directory=True)
    return path


def create_session(provider: str = "mock", mode: str = "interactive", home: str | Path | None = None) -> str:
    session_id = str(uuid4())
    meta = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "session_id": session_id,
        "created_at": now(),
        "updated_at": now(),
        "provider": provider,
        "mode": mode,
        "event_schema_version": CLI_EVENT_SCHEMA_VERSION,
    }
    root = sessions_dir(home)
    atomic_write_json(root / f"{session_id}.meta.json", meta)
    atomic_write_text(root / f"{session_id}.jsonl", "")
    return session_id


def append_event(session_id: str, event: dict, home: str | Path | None = None) -> None:
    sid = validate_session_id(session_id)
    path = sessions_dir(home) / f"{sid}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    set_user_only_permissions(path, directory=False)
    meta_path = sessions_dir(home) / f"{sid}.meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["updated_at"] = now()
        atomic_write_json(meta_path, meta)


def list_sessions(home: str | Path | None = None) -> list[dict]:
    rows = []
    for meta_path in sorted(sessions_dir(home).glob("*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if meta.get("schema_version") == SESSION_SCHEMA_VERSION:
            rows.append(meta)
    return rows


def read_session(session_id: str, home: str | Path | None = None) -> tuple[dict, list[dict]]:
    sid = validate_session_id(session_id)
    root = sessions_dir(home)
    meta_path = root / f"{sid}.meta.json"
    jsonl_path = root / f"{sid}.jsonl"
    if not meta_path.is_file() or not jsonl_path.is_file():
        raise SessionError(f"Session {sid} was not found. Next: agentos session list")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionError("Session metadata is malformed. Next: agentos session list") from exc
    if meta.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise SessionError("Session schema is unsupported. Next: agentos session list")
    events = []
    try:
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if line:
                events.append(json.loads(line))
    except json.JSONDecodeError as exc:
        raise SessionError("Session events are malformed. Next: agentos session list") from exc
    return meta, events


def sessions_before(date_text: str, home: str | Path | None = None) -> list[str]:
    cutoff = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    matched = []
    for meta in list_sessions(home):
        updated = datetime.fromisoformat(meta["updated_at"].replace("Z", "+00:00"))
        if updated < cutoff:
            matched.append(meta["session_id"])
    return matched


def delete_session(session_id: str, home: str | Path | None = None) -> None:
    sid = validate_session_id(session_id)
    root = sessions_dir(home)
    found = False
    for suffix in (".jsonl", ".meta.json"):
        path = root / f"{sid}{suffix}"
        if path.exists():
            path.unlink()
            found = True
    if not found:
        raise SessionError(f"Session {sid} was not found. Next: agentos session list")


def prune_before(date_text: str, home: str | Path | None = None) -> list[str]:
    matched = sessions_before(date_text, home)
    for sid in matched:
        delete_session(sid, home)
    return matched
