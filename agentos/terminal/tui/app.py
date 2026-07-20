from __future__ import annotations

import os

from rich.console import Console
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widgets import Footer, Header, ListItem, Label

from agentos.commands import hook as hook_command
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event
from agentos.terminal.events import CliEvent, new_turn_id, wrap_provider_event
from agentos.terminal.hooks import HookError, apply_input_hooks
from agentos.terminal.interaction import run_interactive
from agentos.terminal.paths import initialize_state
from agentos.terminal.sessions import SessionError, append_event, create_session, read_session, session_summaries
from agentos.terminal.tui.commands import command_palette_text, find_command
from agentos.terminal.tui.renderers import render_event, render_session_summary
from agentos.terminal.tui.state import TuiStatus
from agentos.terminal.tui.widgets import Composer, SessionPicker, StatusFooter, Transcript


class AgentOSTui(App[None]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    Screen {
        layout: vertical;
    }
    """

    def __init__(self, provider: str = "mock", *, create_session_on_start: bool = True) -> None:
        super().__init__()
        self.provider = provider
        initialize_state()
        self.session_id = create_session(provider=provider, mode="tui") if create_session_on_start else ""
        self.status = TuiStatus.initial(provider=provider, session_id=self.session_id)
        self.picker_rows: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Transcript(
            "AgentOS\nType a message or / for commands",
            id="transcript",
        )
        yield Composer(placeholder="Type a message or / for commands", id="composer")
        yield SessionPicker(id="session-picker")
        yield StatusFooter(self.status.footer_text(), id="status")
        yield Footer()

    def on_input_submitted(self, event: Composer.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        transcript = self.query_one("#transcript", Transcript)
        command = find_command(text)
        if text in {"/exit", "exit", "quit"} or (command and command.handler_id == "exit"):
            self.exit(result=None)
            return
        if text == "/" or (command and command.handler_id == "help"):
            transcript.update(
                f"AgentOS\n{command_palette_text()}\nCtrl-C cancels a turn.\n"
                "Esc closes overlays. EOF exits. Shift+Enter inserts a newline."
            )
            return
        if command and command.handler_id == "status":
            transcript.update(self.status.footer_text())
            event.input.focus()
            return
        if command and command.handler_id == "session":
            transcript.update("/session list - List recent sessions\n/session resume - Open the session resume picker")
            event.input.focus()
            return
        if command and command.handler_id == "session_list":
            rows = session_summaries()
            transcript.update("\n".join(render_session_summary(row) for row in rows) if rows else "No sessions found. Esc to return.")
            event.input.focus()
            return
        if command and command.handler_id == "session_resume":
            rows = session_summaries()
            picker = self.query_one("#session-picker", SessionPicker)
            picker.clear()
            self.picker_rows = []
            if not rows:
                transcript.update("No sessions found. Esc to return.")
                event.input.focus()
                return
            available_rows = [row for row in rows if row.get("available", False)]
            for row in rows:
                picker.append(ListItem(Label(render_session_summary(row))))
            self.picker_rows = rows
            if len(rows) > 1:
                transcript.update("Session picker\nEsc to return. Enter to resume selected session.")
                self.call_after_refresh(picker.focus)
                return
            first = available_rows[0] if available_rows else rows[0]
            if not first.get("available", False):
                transcript.update("Session unavailable. Next: /session list")
                event.input.focus()
                return
            self._resume_session(str(first["session_id"]))
            event.input.focus()
            return
        if command and command.handler_id == "hooks":
            transcript.update("Hooks: only existing AgentOS-built hooks are shown.")
            event.input.focus()
            return
        if command and command.handler_id == "clear":
            transcript.update("")
            event.input.focus()
            return
        if text.startswith("/"):
            transcript.update("Unknown command. Next: /help")
            event.input.focus()
            return
        if not self.session_id:
            self.session_id = create_session(provider=self.provider, mode="tui")
            self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id)
            self.query_one("#status", StatusFooter).update(self.status.footer_text())
        turn_id = new_turn_id()
        try:
            prompt = apply_input_hooks(text)
        except HookError:
            self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id).with_last_turn("error")
            self.query_one("#status", StatusFooter).update(self.status.footer_text())
            transcript.update("Hook failed. Next: /hooks")
            event.input.focus()
            return
        append_event(
            self.session_id,
            CliEvent("input_received", self.session_id, turn_id, self.provider, "tui", {"length": len(prompt)}).to_dict(),
        )
        lines = [f"You: {text}"]
        self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id).with_last_turn("running")
        self.query_one("#status", StatusFooter).update(self.status.footer_text())
        try:
            for provider_event in stream_once(prompt, provider=self.provider):
                payload = provider_event.to_dict()
                append_event(
                    self.session_id,
                    wrap_provider_event(
                        payload,
                        session_id=self.session_id,
                        turn_id=turn_id,
                        provider=self.provider,
                        mode="tui",
                    ),
                )
                rendered = render_event(payload)
                if rendered:
                    lines.append(rendered)
                if payload["type"] == "error":
                    self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id).with_last_turn("error")
            if self.status.last_turn != "error":
                self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id).with_last_turn("done")
        except UnsupportedProviderError:
            payload = unsupported_provider_event(self.provider).to_dict()
            append_event(self.session_id, payload)
            lines.append(payload["error"]["message"])
            self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id).with_last_turn("error")
        self.query_one("#status", StatusFooter).update(self.status.footer_text())
        transcript.update("\n".join(lines))
        event.input.focus()

    def on_session_picker_selected(self, event: SessionPicker.Selected) -> None:
        index = event.list_view.index or 0
        self._resume_picker_index(index)

    def on_key(self, event: Key) -> None:
        if self.focused is self.query_one("#session-picker", SessionPicker):
            if event.key == "enter":
                self._resume_picker_index(self.query_one("#session-picker", SessionPicker).index or 0)
                event.stop()
            elif event.key == "escape":
                self.action_cancel()
                event.stop()

    def _resume_picker_index(self, index: int) -> None:
        row = self.picker_rows[index] if 0 <= index < len(self.picker_rows) else None
        transcript = self.query_one("#transcript", Transcript)
        if not row or not row.get("available", False):
            transcript.update("Session unavailable. Next: /session list")
            self.query_one("#composer", Composer).focus()
            return
        self._resume_session(str(row["session_id"]))
        self.query_one("#composer", Composer).focus()

    def action_cancel(self) -> None:
        if self.focused is self.query_one("#session-picker", SessionPicker):
            self.query_one("#transcript", Transcript).update("Resume cancelled.")
            self.query_one("#composer", Composer).focus()
            return
        self.query_one("#composer", Composer).focus()

    def _resume_session(self, session_id: str) -> None:
        transcript = self.query_one("#transcript", Transcript)
        try:
            meta, _ = read_session(session_id)
        except SessionError:
            transcript.update("Session unavailable. Next: /session list")
            return
        self.session_id = meta["session_id"]
        self.provider = meta["provider"]
        self.status = TuiStatus.initial(provider=self.provider, session_id=self.session_id)
        self.query_one("#status", StatusFooter).update(self.status.footer_text())
        transcript.update(f"Resumed session {self.session_id[:8]}.\nSession summary updated.")


def run_tui(provider: str = "mock") -> int:
    if os.environ.get("AGENTOS_TUI_TEST_PLAIN") == "1":
        return run_plain_tui_transcript(provider=provider)
    try:
        AgentOSTui(provider=provider).run()
        return 0
    except Exception:
        Console(stderr=True).print("TUI failed. Falling back to legacy interactive mode.")
        return run_interactive(provider=provider)


def run_plain_tui_transcript(provider: str = "mock") -> int:
    console = Console()
    initialize_state()
    session_id = create_session(provider=provider, mode="tui")
    status = TuiStatus.initial(provider=provider, session_id=session_id)
    console.print("AgentOS")
    console.print("Type a message or / for commands")
    console.print(status.footer_text())
    while True:
        try:
            raw = input("agentos[tui]> ")
        except EOFError:
            console.print("Session closed.")
            return 0
        text = raw.strip()
        command = find_command(text)
        if text in {"/exit", "exit", "quit"} or (command and command.handler_id == "exit"):
            console.print("Session closed.")
            return 0
        if text == "/" or (command and command.handler_id == "help"):
            console.print(command_palette_text())
            console.print("Ctrl-C cancels a turn. Esc closes overlays. EOF exits. Shift+Enter inserts a newline.")
            continue
        if command and command.handler_id == "session":
            console.print("/session list - List recent sessions")
            console.print("/session resume - Open the session resume picker")
            continue
        if command and command.handler_id == "hooks":
            hook_command.list_()
            continue
        if command and command.handler_id == "status":
            console.print(status.footer_text())
            continue
        if command and command.handler_id == "clear":
            console.clear()
            continue
        if text.startswith("/"):
            console.print("Unknown command. Next: /help")
            continue
        turn_id = new_turn_id()
        try:
            prompt = apply_input_hooks(raw)
        except HookError:
            console.print("Hook failed. Next: /hooks")
            continue
        append_event(
            session_id,
            CliEvent("input_received", session_id, turn_id, provider, "tui", {"length": len(prompt)}).to_dict(),
        )
        try:
            for event in stream_once(prompt, provider=provider):
                payload = event.to_dict()
                append_event(
                    session_id,
                    wrap_provider_event(
                        payload,
                        session_id=session_id,
                        turn_id=turn_id,
                        provider=provider,
                        mode="tui",
                    ),
                )
                rendered = render_event(payload)
                if rendered:
                    console.print(rendered)
        except UnsupportedProviderError:
            payload = unsupported_provider_event(provider).to_dict()
            append_event(session_id, payload)
            console.print(payload["error"]["message"])
            return 1
