from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LauncherResolution:
    executable: str | None
    status: str
    installed: bool
    recovery: str

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "canonical": "agentos",
            "development": "uv run agentos",
            "installed_agentos": self.installed,
            "status": self.status,
            "recovery": self.recovery,
        }
        if self.executable is not None:
            payload["executable"] = self.executable
        return payload


def resolve_agentos_launcher() -> LauncherResolution:
    executable = shutil.which("agentos")
    if executable is None:
        return LauncherResolution(
            executable=None,
            status="missing_installed_agentos",
            installed=False,
            recovery=(
                "No `agentos` console script is available on this shell PATH. "
                "Use `uv run agentos ...` for development, or install AgentOS before treating `agentos` as canonical."
            ),
        )

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        try:
            executable_path = Path(executable).resolve()
            venv_bin = (Path(venv).resolve() / "bin")
            executable_path.relative_to(venv_bin)
        except ValueError:
            pass
        else:
            return LauncherResolution(
                executable=executable,
                status="development_shim",
                installed=False,
                recovery=(
                    "`agentos` resolves to the active uv/virtualenv shim, not a shell-installed canonical launcher. "
                    "Use this only as a development path."
                ),
            )

    return LauncherResolution(
        executable=executable,
        status="ok",
        installed=True,
        recovery="Use the installed `agentos` console script as the canonical path.",
    )
