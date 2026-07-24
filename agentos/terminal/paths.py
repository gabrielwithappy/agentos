from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

STATE_SCHEMA_VERSION = "agentos.cli-state/v1"


class StateError(ValueError):
    pass


def agentos_home(home: str | Path | None = None) -> Path:
    raw = Path(home or os.environ.get("AGENTOS_HOME", Path.home() / ".agentos")).expanduser()
    if raw.exists() and raw.is_symlink():
        raise StateError("AGENTOS_HOME must not be a symlink.")
    return raw.resolve(strict=False)


def ensure_contained(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise StateError(f"Path escapes AGENTOS_HOME: {path}") from exc
    return resolved


def set_user_only_permissions(path: Path, directory: bool) -> None:
    try:
        path.chmod(0o700 if directory else 0o600)
    except OSError:
        pass


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    set_user_only_permissions(path.parent, directory=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        set_user_only_permissions(tmp, directory=False)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def initialize_state(home: str | Path | None = None) -> Path:
    root = agentos_home(home)
    root.mkdir(parents=True, exist_ok=True)
    set_user_only_permissions(root, directory=True)
    for dirname in ("sessions", "context"):
        child = root / dirname
        if child.exists() and child.is_symlink():
            raise StateError(f"{dirname} must not be a symlink.")
        child.mkdir(exist_ok=True)
        set_user_only_permissions(child, directory=True)
    config = root / "config.toml"
    if not config.exists():
        atomic_write_text(config, 'schema_version = "agentos.hooks/v1"\n\n[hooks]\n')
    manifest = root / "state-manifest.json"
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8"))
        if existing.get("schema_version") != STATE_SCHEMA_VERSION:
            raise StateError("Existing state manifest has an incompatible schema.")
    atomic_write_json(
        manifest,
        {
            "schema_version": STATE_SCHEMA_VERSION,
            "managed_by": "agentos",
            "directories": ["sessions", "context"],
        },
    )
    return root


def preferred_provider_path(home: str | Path | None = None) -> Path:
    return agentos_home(home) / "preferred-provider.json"


def read_preferred_provider(home: str | Path | None = None) -> str | None:
    path = preferred_provider_path(home)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    provider = payload.get("provider")
    return provider if isinstance(provider, str) and provider else None


def write_preferred_provider(provider: str, home: str | Path | None = None) -> None:
    atomic_write_json(
        preferred_provider_path(home),
        {"schema_version": STATE_SCHEMA_VERSION, "provider": provider},
    )
def state_status(home: str | Path | None = None) -> dict[str, Any]:
    root = agentos_home(home)
    manifest = root / "state-manifest.json"
    payload: dict[str, Any] = {
        "schema_version": STATE_SCHEMA_VERSION,
        "home": str(root),
        "configured": False,
        "sessions_dir": str(root / "sessions"),
        "context_dir": str(root / "context"),
    }
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload["status"] = "invalid_manifest"
            return payload
        payload["configured"] = data.get("schema_version") == STATE_SCHEMA_VERSION
        payload["manifest_schema_version"] = data.get("schema_version")
    payload["status"] = "ok" if payload["configured"] else "not_configured"
    return payload
