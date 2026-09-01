from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from agentos.terminal.paths import StateError, agentos_home, atomic_write_json, set_user_only_permissions

SKILL_MANIFEST_SCHEMA = "agentos.skills/v1"
MANIFEST_NAME = ".agentos-skills.json"
DEFAULT_SKILL_NAMES = (
    "architecture-diagram", "baoyu-infographic", "claude-design",
    "codebase-inspection", "design-md", "frontend-design", "future-slide", "humanizer", "p5js",
    "knowledge-curator", "popular-web-designs", "pretext", "requesting-code-review", "sketch", "spike",
    "systematic-debugging", "codex-imagegen-2", "youtube-transcript", "skill-creator",
    "skill-catalog-viewer",
)


@dataclass(frozen=True)
class SkillStatus:
    name: str
    state: str
    digest: str | None
    source_digest: str | None


@dataclass(frozen=True)
class BundledInstallSummary:
    installed: int = 0
    already_current: int = 0
    bundled_updated: int = 0
    bundled_update_available: int = 0
    custom_preserved: int = 0
    failed: int = 0


def bundled_skill_sources() -> list[Path]:
    root = Path(str(files("catalog").joinpath("skills")))
    sources = {path.name: path for path in root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    if set(sources) != set(DEFAULT_SKILL_NAMES):
        raise StateError("Bundled skill catalog is malformed. Next: reinstall AgentOS")
    ordered = [sources[name] for name in DEFAULT_SKILL_NAMES]
    for source in ordered:
        _require_regular_tree(source)
    return ordered


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


def install_skill(source: str | Path, home: str | Path | None = None, *, origin: str = "external") -> str:
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
    manifest["skills"][name] = {"digest": source_digest, "source": str(source_path), "source_digest": source_digest, "origin": origin}
    atomic_write_json(_manifest_path(home), manifest)
    return name


def install_bundled_skills(home: str | Path | None = None, *, refresh: bool = False) -> BundledInstallSummary:
    result = BundledInstallSummary()
    manifest = _manifest(home)
    root = global_skills_dir(home)
    for source in bundled_skill_sources():
        name = source.name
        try:
            bundle_digest = skill_digest(source)
            dest = root / name
            record = manifest["skills"].get(name, {})
            if not dest.exists():
                install_skill(source, home, origin="bundled")
                result = BundledInstallSummary(**{**result.__dict__, "installed": result.installed + 1})
                continue
            actual = skill_digest(dest)
            if record.get("origin") == "bundled" and actual == record.get("digest"):
                if actual == bundle_digest:
                    result = BundledInstallSummary(**{**result.__dict__, "already_current": result.already_current + 1})
                else:
                    install_skill(source, home, origin="bundled")
                    result = BundledInstallSummary(**{**result.__dict__, "bundled_updated": result.bundled_updated + 1})
            elif refresh:
                install_skill(source, home, origin="bundled")
                result = BundledInstallSummary(**{**result.__dict__, "bundled_updated": result.bundled_updated + 1})
            elif record.get("origin") == "bundled":
                result = BundledInstallSummary(**{**result.__dict__, "bundled_update_available": result.bundled_update_available + 1})
            else:
                result = BundledInstallSummary(**{**result.__dict__, "custom_preserved": result.custom_preserved + 1})
        except (OSError, StateError):
            result = BundledInstallSummary(**{**result.__dict__, "failed": result.failed + 1})
    return result


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


def global_skill_read_paths(home: str | Path | None = None) -> tuple[Path, ...]:
    """`SKILL.md` files under the global skills dir that tools may read even
    though they sit outside the session cwd.

    Shared by the TUI and the interactive CLI so the two front-ends can
    never grant different read boundaries for the same session.
    """
    root = global_skills_dir(home)
    if root.is_symlink() or not root.is_dir():
        return ()
    paths: list[Path] = []
    for entry in root.iterdir():
        skill_file = entry / "SKILL.md"
        if entry.is_symlink() or not entry.is_dir() or skill_file.is_symlink() or not skill_file.is_file():
            continue
        paths.append(skill_file.resolve())
    return tuple(paths)


def project_skill_dirs(cwd: str | Path, home: str | Path | None = None) -> tuple[Path, ...]:
    """Return project-local skills first, followed by the global fallback."""
    project_root = Path(cwd).expanduser().resolve()
    marker = project_root / ".agentos" / "agentos-project" / "manifest.json"
    local = project_root / ".agents" / "skills"
    global_root = global_skills_dir(home)
    result: list[Path] = []
    if marker.is_file() and not marker.is_symlink() and local.is_dir() and not local.is_symlink():
        result.append(local)
    if global_root.is_dir() and not global_root.is_symlink() and global_root not in result:
        result.append(global_root)
    return tuple(result)


def project_skill_read_paths(cwd: str | Path, home: str | Path | None = None) -> tuple[Path, ...]:
    """Return readable project-local and global skill files in precedence order."""
    paths: list[Path] = []
    for root in project_skill_dirs(cwd, home):
        for entry in root.iterdir():
            skill_file = entry / "SKILL.md"
            if entry.is_symlink() or not entry.is_dir() or skill_file.is_symlink() or not skill_file.is_file():
                continue
            resolved = skill_file.resolve()
            if resolved not in paths:
                paths.append(resolved)
    return tuple(paths)
