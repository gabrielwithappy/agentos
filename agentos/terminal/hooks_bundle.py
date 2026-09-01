from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from agentos.terminal.paths import StateError


BUNDLE_SCRIPTS = {
    "check-careful.sh",
    "check-alignment.py",
}


def bundle_script(name: str) -> Path:
    """Return one immutable, package-owned hook script.

    Only the manifest above is addressable.  This prevents a project path or a
    hook payload from selecting arbitrary local executables.
    """
    if name not in BUNDLE_SCRIPTS:
        raise StateError(f"Unsupported bundled hook script: {name}")
    resource = files("agentos").joinpath("_hooks_bundle", "hooks", "scripts", name)
    try:
        path = Path(resource)
    except TypeError as exc:  # pragma: no cover - wheels are installed unpacked
        raise StateError("Bundled hook resources must be installed as regular files.") from exc
    if not path.is_file() or path.is_symlink():
        raise StateError(f"Bundled hook resource is not a regular file: {name}")
    return path
