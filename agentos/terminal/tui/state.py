from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.cells import cell_len


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
    conversation_branch: str | None = None

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
        conversation_branch: str | None = None,
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
            conversation_branch=conversation_branch,
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
            conversation_branch=self.conversation_branch,
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
            conversation_branch=self.conversation_branch,
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
        if self.conversation_branch is not None:
            # Distinct from the git `branch` label above: this is the
            # active *conversation* branch (fork/resume target), not a git ref.
            parts.append(f"convo-branch {shorten(self.conversation_branch)}")
        parts.append(f"total in/out {self.total_input_chars}/{self.total_output_chars} chars")
        return " | ".join(parts)

    def compact_footer_parts(self, max_width: int = 80) -> list[tuple[str, str]]:
        """Return a one-line, terminal-cell-width-aware TUI footer.

        The detailed ``footer_text`` contract remains for /status and the
        non-Textual fallback.  Here, optional location/branch details yield
        first on narrow screens; turn, provider/session, and usage remain.
        """
        if max_width < 1:
            return []

        fields: list[tuple[str, str, bool]] = [
            ("cwd:", self.cwd, True),
            ("pm:", f"{self.provider}/{self.model}", False),
            ("sid:", self.session, False),
        ]
        if self.git_branch:
            fields.append(("git:", self.git_branch, True))
        if self.conversation_branch:
            fields.append(("convo:", self.conversation_branch, True))
        fields.extend([
            ("turn:", self.last_turn, False),
            ("in:", str(self.total_input_chars), False),
            ("out:", str(self.total_output_chars), False),
        ])

        def width(items: list[tuple[str, str, bool]]) -> int:
            return cell_len(" ".join(f"{label}{value}" for label, value, _ in items))

        # Omit optional fields from lowest priority first.
        for label in ("cwd:", "convo:", "git:"):
            if width(fields) <= max_width:
                break
            fields = [field for field in fields if field[0] != label]

        # Then make values shorter without splitting wide characters.
        shrink_order = ("pm:", "sid:", "out:", "in:", "turn:")
        while width(fields) > max_width:
            changed = False
            for label in shrink_order:
                for index, (field_label, value, optional) in enumerate(fields):
                    if field_label == label and cell_len(value) > 1:
                        fields[index] = (field_label, _truncate_cells(value, cell_len(value) - 1), optional)
                        changed = True
                        break
                if changed:
                    break
            if not changed:
                break
        # Extremely narrow terminals cannot fit the mandatory labels alone.
        # Return a single deterministic ellipsized fragment rather than
        # relying on Textual to clip or wrap beyond the screen edge.
        if width(fields) > max_width:
            return [("", _truncate_cells(" ".join(f"{label}{value}" for label, value, _ in fields), max_width))]
        return [(label, value) for label, value, _ in fields]

    def compact_footer_text(self, max_width: int = 80) -> str:
        return " ".join(f"{label}{value}" for label, value in self.compact_footer_parts(max_width))


def _truncate_cells(value: str, max_width: int) -> str:
    """Truncate without exceeding terminal-cell width, using an ellipsis."""
    if cell_len(value) <= max_width:
        return value
    if max_width <= 1:
        return "…" if max_width else ""
    kept = ""
    for character in value:
        if cell_len(kept + character) > max_width - 1:
            break
        kept += character
    return kept + "…"


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
