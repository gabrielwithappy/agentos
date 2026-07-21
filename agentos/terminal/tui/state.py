from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TuiStatus:
    cwd: str
    provider: str
    model: str
    session: str
    hooks: str
    mode: str = "tui"
    last_turn: str = "idle"
    max_value_width: int = 24
    git_branch: str | None = None
    total_input_chars: int = 0
    total_output_chars: int = 0

    @classmethod
    def initial(
        cls,
        *,
        provider: str,
        session_id: str,
        hook_count: int = 0,
        cwd: Path | None = None,
        git_branch: str | None = None,
        total_input_chars: int = 0,
        total_output_chars: int = 0,
    ) -> "TuiStatus":
        current = cwd or Path.cwd()
        home = Path.home()
        try:
            display_cwd = "~" / current.relative_to(home)
        except ValueError:
            display_cwd = current
        return cls(
            cwd=str(display_cwd),
            provider=provider if provider else "?",
            model="mock" if provider == "mock" else "?",
            session=session_id[:8] if session_id else "new",
            hooks=str(hook_count),
            git_branch=git_branch,
            total_input_chars=total_input_chars,
            total_output_chars=total_output_chars,
        )

    def with_last_turn(self, value: str) -> "TuiStatus":
        return TuiStatus(
            cwd=self.cwd,
            provider=self.provider,
            model=self.model,
            session=self.session,
            hooks=self.hooks,
            mode=self.mode,
            last_turn=value,
            max_value_width=self.max_value_width,
            git_branch=self.git_branch,
            total_input_chars=self.total_input_chars,
            total_output_chars=self.total_output_chars,
        )

    def with_totals(self, input_chars: int, output_chars: int) -> "TuiStatus":
        return TuiStatus(
            cwd=self.cwd,
            provider=self.provider,
            model=self.model,
            session=self.session,
            hooks=self.hooks,
            mode=self.mode,
            last_turn=self.last_turn,
            max_value_width=self.max_value_width,
            git_branch=self.git_branch,
            total_input_chars=input_chars,
            total_output_chars=output_chars,
        )

    def footer_text(self) -> str:
        def shorten(value: str) -> str:
            if len(value) <= self.max_value_width:
                return value
            if self.max_value_width <= 1:
                return value[: self.max_value_width]
            return value[: self.max_value_width - 1] + "…"

        parts = [
            f"cwd {shorten(self.cwd)}",
            f"provider {shorten(self.provider)}",
            f"model {shorten(self.model)}",
            f"session {shorten(self.session)}",
            f"hooks {shorten(self.hooks)}",
            f"mode {shorten(self.mode)}",
            f"last turn {shorten(self.last_turn)}",
        ]
        if self.git_branch is not None:
            parts.append(f"branch {shorten(self.git_branch)}")
        parts.append(f"total in/out {self.total_input_chars}/{self.total_output_chars} chars")
        return " | ".join(parts)


def get_git_branch() -> str | None:
    """Return the current git branch name, or None on any failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            timeout=1,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            return branch if branch else None
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None
