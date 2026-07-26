from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from agentos.terminal.paths import StateError, agentos_home, atomic_write_json, set_user_only_permissions

SKILL_MANIFEST_SCHEMA = "agentos.skills/v1"
MANIFEST_NAME = ".agentos-skills.json"


@dataclass(frozen=True)
class SkillStatus:
    name: str
    state: str
    digest: str | None
    source_digest: str | None


def global_skills_dir(home: str | Path | None = None) -> Path:
    return agentos_home(home) / "core" / ".agents" / "skills"


def _require_regular_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise StateError("Skill source must be a regular directory.")
    for path in root.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise StateError("Skill source must not contain symlinks or special files.")


def skill_digest(root: Path) -> str:
    _require_regular_tree(root)
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _manifest_path(home: str | Path | None = None) -> Path:
    return global_skills_dir(home) / MANIFEST_NAME


def _manifest(home: str | Path | None = None) -> dict:
    path = _manifest_path(home)
    if not path.exists():
        return {"schema_version": SKILL_MANIFEST_SCHEMA, "skills": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError("Skill manifest is malformed. Next: agentos setup") from exc
    if data.get("schema_version") != SKILL_MANIFEST_SCHEMA or not isinstance(data.get("skills"), dict):
        raise StateError("Skill manifest schema is unsupported. Next: agentos setup")
    return data


def install_skill(source: str | Path, home: str | Path | None = None) -> str:
    source_path = Path(source).expanduser().resolve()
    if not (source_path / "SKILL.md").is_file():
        raise StateError("Skill source must contain SKILL.md.")
    source_digest = skill_digest(source_path)
    root = global_skills_dir(home)
    if root.is_symlink() or not root.is_dir():
        raise StateError("Skills directory not found. Next: agentos setup")
    name = source_path.name
    if name in {"", ".", ".."} or "/" in name:
        raise StateError("Invalid skill name.")
    stage = Path(tempfile.mkdtemp(prefix=f".{name}.stage-", dir=root))
    backup = root / f".{name}.backup"
    dest = root / name
    try:
        shutil.rmtree(stage)
        shutil.copytree(source_path, stage)
        if skill_digest(stage) != source_digest:
            raise StateError("Staged skill validation failed.")
        if backup.exists():
            shutil.rmtree(backup)
        if dest.exists():
            if dest.is_symlink() or not dest.is_dir():
                raise StateError("Installed skill destination is invalid.")
            os.replace(dest, backup)
        try:
            os.replace(stage, dest)
        except OSError:
            if backup.exists() and not dest.exists():
                os.replace(backup, dest)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    manifest = _manifest(home)
    manifest["skills"][name] = {"digest": source_digest, "source": str(source_path), "source_digest": source_digest}
    atomic_write_json(_manifest_path(home), manifest)
    return name


def statuses(home: str | Path | None = None) -> list[SkillStatus]:
    root = global_skills_dir(home)
    manifest = _manifest(home)
    result: list[SkillStatus] = []
    for name, record in sorted(manifest["skills"].items()):
        installed = root / name
        try:
            actual = skill_digest(installed)
        except StateError:
            result.append(SkillStatus(name, "invalid", None, record.get("source_digest")))
            continue
        source = Path(record.get("source", ""))
        if not source.is_dir():
            state, source_digest = "source_unavailable", record.get("source_digest")
        else:
            try:
                source_digest = skill_digest(source)
                state = "current" if actual == source_digest == record.get("digest") else "stale"
            except StateError:
                state, source_digest = "source_unavailable", None
        result.append(SkillStatus(name, state, actual, source_digest))
    return result
