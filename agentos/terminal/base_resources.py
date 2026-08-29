from __future__ import annotations

import json
import os
import shutil
import tempfile
from hashlib import sha256
from importlib.resources import files
from pathlib import Path

from agentos.terminal.paths import StateError, atomic_write_json

BASE_MANIFEST_SCHEMA = "agentos.harness-base/v1"
BASE_MANIFEST_NAME = ".agentos-harness.json"


def _source_checkout_root() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    if (root / "pyproject.toml").is_file() and (root / ".agents" / "agents" / "harness").is_dir():
        return root
    return None


def _packaged_harness_root() -> Path | None:
    root = Path(str(files("agentos").joinpath("_harness_bundle")))
    return root if root.is_dir() else None


def harness_sources() -> tuple[Path, Path]:
    root = _source_checkout_root()
    if root is not None:
        agents = root / ".agents" / "agents" / "harness"
        skills = root / ".agents" / "skills" / "harness"
    else:
        packaged = _packaged_harness_root()
        if packaged is None:
            raise StateError("Harness base resources are unavailable. Next: reinstall AgentOS")
        agents = packaged / "agents" / "harness"
        skills = packaged / "skills" / "harness"
    if not agents.is_dir() or not skills.is_dir():
        raise StateError("Harness base resources are malformed. Next: reinstall AgentOS")
    return agents, skills


def resource_digest(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise StateError(f"Harness resource is invalid: {root}")
    digest = sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink():
            raise StateError(f"Harness resource contains a symlink: {path}")
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def harness_manifest(agents: Path, skills: Path) -> dict:
    return {
        "schema_version": BASE_MANIFEST_SCHEMA,
        "agents": {"harness": resource_digest(agents)},
        "skills": {"harness": resource_digest(skills)},
    }


def install_harness_base(home: str | Path | None = None) -> dict:
    from agentos.terminal.paths import agentos_home

    agents_source, skills_source = harness_sources()
    # Validate the package/checkout source before any filesystem mutation.
    source_manifest = harness_manifest(agents_source, skills_source)
    root = agentos_home(home) / "core" / ".agents"
    agents_target, skills_target = root / "agents" / "harness", root / "skills" / "harness"
    root.mkdir(parents=True, exist_ok=True)
    for target in (root / "agents", root / "skills"):
        if target.exists() and (target.is_symlink() or not target.is_dir()):
            raise StateError(f"Harness destination is invalid: {target}")
        target.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".harness-base-stage-", dir=root))
    try:
        shutil.copytree(agents_source, stage / "agents")
        shutil.copytree(skills_source, stage / "skills")
        manifest = harness_manifest(stage / "agents", stage / "skills")
        if manifest != source_manifest:
            raise StateError("Harness base staging validation failed.")
        for source, target in ((stage / "agents", agents_target), (stage / "skills", skills_target)):
            backup = target.parent / f".{target.name}.agentos-backup"
            if backup.exists():
                shutil.rmtree(backup)
            if target.exists():
                os.replace(target, backup)
            try:
                os.replace(source, target)
            except OSError:
                if backup.exists() and not target.exists():
                    os.replace(backup, target)
                raise
            if backup.exists():
                shutil.rmtree(backup)
        atomic_write_json(root / BASE_MANIFEST_NAME, manifest)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def read_harness_manifest(home: str | Path | None = None) -> dict:
    from agentos.terminal.paths import agentos_home

    path = agentos_home(home) / "core" / ".agents" / BASE_MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise StateError("Harness base manifest is missing. Next: agentos setup")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError("Harness base manifest is malformed. Next: agentos setup") from exc
    if data.get("schema_version") != BASE_MANIFEST_SCHEMA or not isinstance(data.get("agents"), dict) or not isinstance(data.get("skills"), dict):
        raise StateError("Harness base manifest schema is unsupported. Next: agentos setup")
    return data
