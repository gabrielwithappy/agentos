from __future__ import annotations

import os

from rich.console import Console
from textual import work
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
from agentos.terminal.tui.renderers import format_tool_summary, render_event, render_session_summary
from agentos.terminal.tui.state import TuiStatus, get_git_branch
from agentos.terminal.tui.widgets import ChatMessage, CommandPaletteScreen, Composer, SessionPicker, StatusFooter, ThemeScreen, Transcript

# Keyboard shortcut reference table shown by /hotkeys
_HOTKEYS_TABLE = """\
Keyboard Shortcuts
──────────────────────────────────────────────────
  Enter             Submit message
  Shift+Enter       Insert newline
  Up / Down         Navigate history (at line start/end)
  Ctrl+K            Kill to end of line
  Ctrl+U            Kill to start of line
  Ctrl+W / Alt+BS   Kill word left
  Ctrl+Y            Yank (paste killed text)
  Ctrl+Z            Undo
  Tab               Open command palette (when line starts with /)
  Ctrl+B            Open menu
  Esc               Cancel / close overlay
  Ctrl+C / EOF      Exit
──────────────────────────────────────────────────
"""


class AgentOSTui(App[None]):
    BINDINGS = [("escape", "cancel", "Cancel"), ("ctrl+b", "open_menu", "Menu")]

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
        # Cumulative usage counters — owned by app instance so TuiStatus.initial() re-creation never resets them
        self.total_input_chars: int = 0
        self.total_output_chars: int = 0
        # Git branch: queried once at startup and cached (branch rarely changes during a session)
        self.git_branch: str | None = get_git_branch()
        self.status = self._status_with_totals(provider=provider, session_id=self.session_id)
        self.picker_rows: list[dict] = []
        self.last_tool_calls: list[dict[str, object]] = []
        self.last_usage: dict[str, int] | None = None

    def _status_with_totals(
        self,
        *,
        provider: str,
        session_id: str,
        hook_count: int = 0,
        last_turn: str | None = None,
    ) -> TuiStatus:
        """Build a TuiStatus that always carries the current cumulative counters and git branch."""
        base = TuiStatus.initial(
            provider=provider,
            session_id=session_id,
            hook_count=hook_count,
            git_branch=self.git_branch,
            total_input_chars=self.total_input_chars,
            total_output_chars=self.total_output_chars,
        )
        if last_turn is not None:
            return base.with_last_turn(last_turn)
        return base

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Transcript(
            "AgentOS\nType a message or / for commands",
            id="transcript",
        )
        yield Composer(id="composer")
        yield SessionPicker(id="session-picker")
        yield StatusFooter(self.status.footer_text(), id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._focus_composer()

    def _focus_composer(self) -> None:
        self.query_one("#composer", Composer).focus()

    def on_composer_submitted(self, event: Composer.Submitted) -> None:
        text = event.value.strip()
        event.input.reset_editor_state()
        self.process_input(text)

    def on_composer_completion_requested(self, event: Composer.CompletionRequested) -> None:
        self._open_command_palette(event.value)

    def _open_command_palette(self, prefix: str = "") -> None:
        composer = self.query_one("#composer", Composer)

        def palette_callback(command: str) -> None:
            if command:
                composer.text = f"{command} "
            composer.focus()

        self.push_screen(CommandPaletteScreen(prefix), palette_callback)

    def process_input(self, text: str) -> None:
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
        if command and command.handler_id == "hotkeys":
            transcript.update(_HOTKEYS_TABLE)
            self._focus_composer()
            return
        if command and command.handler_id == "theme":
            self._open_theme_picker()
            return
        if command and command.handler_id == "status":
            transcript.update(self.status.footer_text())
            self._focus_composer()
            return
        if command and command.handler_id == "session":
            transcript.update("/session list - List recent sessions\n/session resume - Open the session resume picker")
            self._focus_composer()
            return
        if command and command.handler_id == "session_list":
            rows = session_summaries()
            transcript.update("\n".join(render_session_summary(row) for row in rows) if rows else "No sessions found. Esc to return.")
            self._focus_composer()
            return
        if command and command.handler_id == "session_resume":
            rows = session_summaries()
            picker = self.query_one("#session-picker", SessionPicker)
            picker.clear()
            self.picker_rows = []
            if not rows:
                transcript.update("No sessions found. Esc to return.")
                self._focus_composer()
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
                self._focus_composer()
                return
            self._resume_session(str(first["session_id"]))
            self._focus_composer()
            return
        if command and command.handler_id == "hooks":
            transcript.update("Hooks: only existing AgentOS-built hooks are shown.")
            self._focus_composer()
            return
        if command and command.handler_id == "tools":
            transcript.update(self._tools_summary())
            self._focus_composer()
            return
        if command and command.handler_id == "usage":
            transcript.update(self._usage_summary())
            self._focus_composer()
            return
        if command and command.handler_id == "clear":
            transcript.update("")
            self._focus_composer()
            return
        if text.startswith("/"):
            transcript.update("Unknown command. Next: /help")
            self._focus_composer()
            return
        if not self.session_id:
            self.session_id = create_session(provider=self.provider, mode="tui")
            self.status = self._status_with_totals(provider=self.provider, session_id=self.session_id)
            self.query_one("#status", StatusFooter).update(self.status.footer_text())
        turn_id = new_turn_id()
        try:
            prompt = apply_input_hooks(text)
        except HookError:
            self.status = self._status_with_totals(provider=self.provider, session_id=self.session_id, last_turn="error")
            self.query_one("#status", StatusFooter).update(self.status.footer_text())
            transcript.update("Hook failed. Next: /hooks")
            self._focus_composer()
            return
        append_event(
            self.session_id,
            CliEvent("input_received", self.session_id, turn_id, self.provider, "tui", {"length": len(prompt)}).to_dict(),
        )
        self.status = self._status_with_totals(provider=self.provider, session_id=self.session_id, last_turn="running")
        self.query_one("#status", StatusFooter).update(self.status.footer_text())
        self.last_tool_calls = []
        self.last_usage = None
        transcript.add_message("user", text)
        self.run_stream(prompt, turn_id, self.session_id, self.provider)
        self._focus_composer()

    def _open_theme_picker(self) -> None:
        themes = sorted(self.available_themes.keys())

        def theme_callback(selected: str) -> None:
            if selected:
                self.theme = selected
            self.query_one("#composer", Composer).focus()

        self.push_screen(ThemeScreen(themes), theme_callback)

    def _update_status(self, status: TuiStatus) -> None:
        self.status = status
        self.query_one("#status", StatusFooter).update(status.footer_text())

    def _tools_summary(self) -> str:
        if not self.last_tool_calls:
            return "No tool calls in the last turn. Next: send a message that needs a tool."
        lines = [
            format_tool_summary(str(call.get("name", "tool")), call.get("arguments"), str(call.get("result", "")))
            for call in self.last_tool_calls
        ]
        return "\n".join(["Tools used in the last turn:", *lines])

    def _usage_summary(self) -> str:
        if not self.last_usage:
            return "No usage yet. Next: send a message."
        input_chars = self.last_usage.get("input_chars", 0)
        output_chars = self.last_usage.get("output_chars", 0)
        return f"Last turn usage: input {input_chars} chars, output {output_chars} chars"

    def _record_turn_results(self, tool_calls: list[dict[str, object]], usage: dict[str, int] | None) -> None:
        self.last_tool_calls = tool_calls
        if usage:
            self.last_usage = usage
            # Accumulate cumulative usage — never reset between turns
            self.total_input_chars += usage.get("input_chars", 0)
            self.total_output_chars += usage.get("output_chars", 0)

    @work(thread=True)
    def run_stream(self, prompt: str, turn_id: str, session_id: str, provider: str) -> None:
        has_error = False
        response_text = ""
        assistant_message: ChatMessage | None = None
        tool_calls: list[dict[str, object]] = []
        usage: dict[str, int] | None = None

        def add_reasoning_message(text_content: str) -> None:
            self.query_one("#transcript", Transcript).add_message("reasoning", text_content)

        def add_tool_message(text_content: str) -> None:
            self.query_one("#transcript", Transcript).add_message("tool", text_content)

        def add_assistant_message() -> ChatMessage:
            return self.query_one("#transcript", Transcript).add_message("assistant", "")

        def update_assistant(text_content: str, *, markdown: bool = False) -> None:
            if assistant_message is not None:
                self.query_one("#transcript", Transcript).update_message(
                    assistant_message,
                    text_content,
                    markdown=markdown,
                )

        import time
        last_update_time = 0.0

        try:
            for provider_event in stream_once(prompt, provider=provider):
                payload = provider_event.to_dict()
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
                event_type = payload["type"]
                if event_type in ("reasoning", "tool_call", "tool_result"):
                    metadata = payload.get("metadata") or {}
                    if event_type == "tool_call":
                        tool_calls.append(
                            {"name": metadata.get("name", "tool"), "arguments": metadata.get("arguments"), "result": ""}
                        )
                    elif event_type == "tool_result" and tool_calls:
                        tool_calls[-1]["result"] = metadata.get("summary", "")
                    rendered = render_event(payload)
                    if rendered:
                        if event_type == "reasoning":
                            self.call_from_thread(add_reasoning_message, rendered)
                        else:
                            # tool_call or tool_result — bordered display
                            self.call_from_thread(add_tool_message, rendered)
                    continue
                if event_type == "message_delta":
                    if assistant_message is None:
                        assistant_message = self.call_from_thread(add_assistant_message)
                    rendered = render_event(payload)
                    if rendered:
                        response_text += rendered
                        now = time.monotonic()
                        if now - last_update_time > 0.05:
                            self.call_from_thread(update_assistant, response_text)
                            last_update_time = now
                    continue
                if event_type == "error":
                    has_error = True
                    self.call_from_thread(
                        self._update_status,
                        self._status_with_totals(provider=provider, session_id=session_id, last_turn="error"),
                    )
                    continue
                if event_type == "done":
                    usage = payload.get("usage")
            if not has_error:
                if assistant_message is not None:
                    self.call_from_thread(update_assistant, response_text, markdown=True)
                self.call_from_thread(self._record_turn_results, tool_calls, usage)
                self.call_from_thread(
                    self._update_status,
                    self._status_with_totals(provider=provider, session_id=session_id, last_turn="done"),
                )
        except UnsupportedProviderError:
            payload = unsupported_provider_event(provider).to_dict()
            append_event(session_id, payload)
            response_text += payload["error"]["message"]
            if assistant_message is None:
                assistant_message = self.call_from_thread(add_assistant_message)
            self.call_from_thread(update_assistant, response_text)
            self.call_from_thread(
                self._update_status,
                self._status_with_totals(provider=provider, session_id=session_id, last_turn="error"),
            )

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
        self.status = self._status_with_totals(provider=self.provider, session_id=self.session_id)
        self.query_one("#status", StatusFooter).update(self.status.footer_text())
        transcript.update(f"Resumed session {self.session_id[:8]}.\nSession summary updated.")

    def action_open_menu(self) -> None:
        def menu_callback(command: str) -> None:
            if command:
                self.process_input(command)
            else:
                self.query_one("#composer", Composer).focus()

        from agentos.terminal.tui.widgets import MenuScreen

        self.push_screen(MenuScreen(), menu_callback)


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
        if command and command.handler_id == "hotkeys":
            console.print(_HOTKEYS_TABLE)
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
