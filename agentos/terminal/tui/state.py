from __future__ import annotations

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

    @classmethod
    def initial(cls, *, provider: str, session_id: str, hook_count: int = 0, cwd: Path | None = None) -> "TuiStatus":
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
        )

    def footer_text(self) -> str:
        def shorten(value: str) -> str:
            if len(value) <= self.max_value_width:
                return value
            if self.max_value_width <= 1:
                return value[: self.max_value_width]
            return value[: self.max_value_width - 1] + "…"

        return (
            f"cwd {shorten(self.cwd)} | provider {shorten(self.provider)} | model {shorten(self.model)} | "
            f"session {shorten(self.session)} | hooks {shorten(self.hooks)} | "
            f"mode {shorten(self.mode)} | last turn {shorten(self.last_turn)}"
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
        )
