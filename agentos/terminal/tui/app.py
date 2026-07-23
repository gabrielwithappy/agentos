from __future__ import annotations

import os

from rich.console import Console
from textual import work
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widgets import Footer, Header, ListItem, Label
from textual.worker import Worker, get_current_worker

from agentos.commands import hook as hook_command
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event
from agentos.terminal.events import CliEvent, new_turn_id, wrap_provider_event
from agentos.terminal.hooks import HookError, apply_input_hooks
from agentos.terminal.interaction import run_interactive
from agentos.terminal.paths import initialize_state
from agentos.terminal.sessions import SessionError, append_event, create_session, read_session, session_summaries
from agentos.terminal.tui.commands import command_palette_text, find_command
from agentos.terminal.tui.renderers import format_tool_summary, render_event, render_session_summary, render_turn_tree
from agentos.terminal.tui.state import TuiStatus, get_git_branch
from agentos.terminal.tui.widgets import ChatMessage, CommandPaletteScreen, Composer, SessionPicker, SpinnerMessage, StatusFooter, ThemeScreen, Transcript

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
  Tab / Shift+Tab   Move focus to messages (Composer <-> newest..oldest)
  c                 Copy focused message to clipboard
  f                 Fork a new branch from focused message
  Ctrl+B            Open menu
  Esc               Cancel turn (while waiting) / close overlay
  Ctrl+C / EOF      Exit
──────────────────────────────────────────────────
"""


def _has_open_code_block(text: str) -> bool:
    """Return True if text contains an unmatched (open) fenced code block.

    Uses fence-line counting (lines starting with ```) instead of backtick character
    count to avoid false positives from inline code spans.
    """
    fence_line_count = sum(
        1 for line in text.splitlines() if line.lstrip().startswith("```")
    )
    return fence_line_count % 2 != 0


def _has_complete_markdown_block(text: str) -> bool:
    """Return True if text has at least one complete code/table block and no open fence."""
    if _has_open_code_block(text):
        return False
    # Has a complete code block
    if text.count("```") >= 2:
        return True
    # Has a complete markdown table (two lines with | separators)
    table_lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    return len(table_lines) >= 2


def _render_streaming_markdown(text: str) -> str:
    """For streaming display: return the accumulated text as-is.

    The caller decides whether to render as markdown based on _has_complete_markdown_block.
    """
    return text


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
        self._active_turn_worker: Worker | None = None
        self._loading_message: ChatMessage | None = None
        self._last_turn_id: str | None = None
        self._indicator_style: str = "ascii"  # ascii | unicode | emoji | kaomoji
        self._pending_parent_turn_id: str | None = None  # set by fork action

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

    # ── Notification helpers (Milestone 1) ──────────────────────────────────

    def _notify_error(self, msg: str) -> None:
        """Show a transient error banner at the top of the screen."""
        self.notify(msg, severity="error", timeout=5)

    def _notify_info(self, msg: str) -> None:
        """Show a transient info banner at the top of the screen."""
        self.notify(msg, severity="information", timeout=3)

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
                "Esc cancels a waiting turn or closes overlays. EOF exits. Shift+Enter inserts a newline."
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
        if command and command.handler_id == "tree":
            transcript.update(self._turn_tree_summary())
            self._focus_composer()
            return
        if command and command.handler_id == "indicator":
            self._handle_indicator(text, transcript)
            return
        if command and command.handler_id == "model":
            self._handle_model(text, transcript)
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
        except HookError as exc:
            self.status = self._status_with_totals(provider=self.provider, session_id=self.session_id, last_turn="error")
            self.query_one("#status", StatusFooter).update(self.status.footer_text())
            self._notify_error(f"Hook failed: {exc}. See /hooks for details.")
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
        pending_parent = self._pending_parent_turn_id
        self._pending_parent_turn_id = None
        transcript.add_message("user", text)
        self._loading_message = transcript.add_message("spinner", "", style=self._indicator_style)
        self._active_turn_worker = self.run_stream(prompt, turn_id, self.session_id, self.provider, pending_parent)
        self._focus_composer()

    def _set_last_turn_id(self, turn_id: str) -> None:
        self._last_turn_id = turn_id

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

    def _clear_loading_message(self) -> None:
        if self._loading_message is not None:
            self.query_one("#transcript", Transcript).remove_message(self._loading_message)
            self._loading_message = None

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

    def _turn_tree_summary(self) -> str:
        if not self.session_id:
            return "No turns yet. Next: send a message."
        try:
            _, events = read_session(self.session_id)
        except SessionError:
            return "No turns yet. Next: send a message."
        return render_turn_tree(events)

    def _record_turn_results(self, tool_calls: list[dict[str, object]], usage: dict[str, int] | None) -> None:
        self.last_tool_calls = tool_calls
        if usage:
            self.last_usage = usage
            # Accumulate cumulative usage — never reset between turns
            self.total_input_chars += usage.get("input_chars", 0)
            self.total_output_chars += usage.get("output_chars", 0)

    # ── Indicator style handler (Milestone 2) ─────────────────────────────

    _VALID_INDICATOR_STYLES = frozenset({"ascii", "unicode", "emoji", "kaomoji"})

    def _handle_indicator(self, text: str, transcript: Transcript) -> None:
        arg = text[len("/indicator"):].strip().lower()
        if not arg:
            transcript.update(
                f"Current indicator style: {self._indicator_style}\n"
                "Styles: ascii | unicode | emoji | kaomoji\n"
                "Usage: /indicator [style]"
            )
            self._focus_composer()
            return
        if arg not in self._VALID_INDICATOR_STYLES:
            self._notify_error(f"Unknown indicator style: {arg!r}. Choose: ascii | unicode | emoji | kaomoji")
            self._focus_composer()
            return
        self._indicator_style = arg
        self._notify_info(f"Indicator style changed to: {arg}")
        self._focus_composer()

    # ── Model picker handler (Milestone 5) ────────────────────────────────

    _AVAILABLE_PROVIDERS = ("mock", "codex")

    def _handle_model(self, text: str, transcript: Transcript) -> None:
        arg = text[len("/model"):].strip().lower()
        if not arg:
            available = " | ".join(self._AVAILABLE_PROVIDERS)
            transcript.update(
                f"Current provider: {self.provider}\n"
                f"Available: {available}\n"
                "Usage: /model [provider]"
            )
            self._focus_composer()
            return
        if arg not in self._AVAILABLE_PROVIDERS:
            self._notify_error(f"Unknown provider: {arg!r}. Available: {' | '.join(self._AVAILABLE_PROVIDERS)}")
            self._focus_composer()
            return
        old = self.provider
        self.provider = arg
        self._notify_info(f"Provider switched: {old} → {arg}")
        self._focus_composer()

    # ── Fork / branch handler (Milestone 4) ──────────────────────────────

    def on_transcript_fork_requested(self, event: Transcript.ForkRequested) -> None:
        """Set pending parent_turn_id so the next submitted message forks from this turn."""
        self._pending_parent_turn_id = event.turn_id
        self._notify_info(f"Forking from turn {event.turn_id[:8]}… Type your message to create a branch.")
        self._focus_composer()

    @work(thread=True)
    def run_stream(self, prompt: str, turn_id: str, session_id: str, provider: str, pending_parent_turn_id: str | None = None) -> None:
        has_error = False
        response_text = ""
        assistant_message: ChatMessage | None = None
        tool_calls: list[dict[str, object]] = []
        usage: dict[str, int] | None = None
        loading_active = True
        worker = get_current_worker()
        parent_turn_id = pending_parent_turn_id if pending_parent_turn_id is not None else self._last_turn_id

        def add_reasoning_message(text_content: str) -> None:
            self.query_one("#transcript", Transcript).add_message("reasoning", text_content)

        def add_tool_message(text_content: str) -> None:
            self.query_one("#transcript", Transcript).add_message("tool", text_content)

        def add_assistant_message() -> ChatMessage:
            return self.query_one("#transcript", Transcript).add_message("assistant", "", turn_id=turn_id)

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
                if worker.is_cancelled:
                    return
                payload = provider_event.to_dict()
                append_event(
                    session_id,
                    wrap_provider_event(
                        payload,
                        session_id=session_id,
                        turn_id=turn_id,
                        provider=provider,
                        mode="tui",
                        parent_turn_id=parent_turn_id,
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
                        if loading_active and event_type in ("reasoning", "tool_call"):
                            self.call_from_thread(self._clear_loading_message)
                            loading_active = False
                        if event_type == "reasoning":
                            self.call_from_thread(add_reasoning_message, rendered)
                        else:
                            # tool_call or tool_result — bordered display
                            self.call_from_thread(add_tool_message, rendered)
                    continue
                if event_type == "message_delta":
                    if loading_active:
                        self.call_from_thread(self._clear_loading_message)
                        loading_active = False
                    if assistant_message is None:
                        assistant_message = self.call_from_thread(add_assistant_message)
                    rendered = render_event(payload)
                    if rendered:
                        response_text += rendered
                        now = time.monotonic()
                        if now - last_update_time > 0.05:
                            # Streaming markdown: render completed blocks immediately
                            partial_text = _render_streaming_markdown(response_text)
                            self.call_from_thread(update_assistant, partial_text, markdown=_has_complete_markdown_block(response_text))
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
            if worker.is_cancelled:
                return
            self.call_from_thread(self._set_last_turn_id, turn_id)
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
            if loading_active:
                self.call_from_thread(self._clear_loading_message)
                loading_active = False
            if assistant_message is None:
                assistant_message = self.call_from_thread(add_assistant_message)
            self.call_from_thread(update_assistant, response_text)
            self.call_from_thread(self._set_last_turn_id, turn_id)
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

    def action_focus_next(self) -> None:
        """Override Screen's default tab->focus_next binding (app.py:270-271 in Textual's
        screen.py) to cycle Composer/messages newest-first instead of DOM mount order.

        A plain Tab press is never stopped by Composer/TextArea (default
        tab_behavior="focus"), so it bubbles to App._on_key, which resolves the
        Screen-level "tab" binding to this action *before* App.on_key would ever
        run — overriding on_key alone cannot intercept Tab; the action itself
        must be overridden. Falls back to the default DOM-order behavior when
        focus isn't on Composer or a transcript message (e.g. SessionPicker).
        """
        if not self._cycle_transcript_focus("tab"):
            super().action_focus_next()

    def action_focus_previous(self) -> None:
        """Shift+Tab counterpart to action_focus_next — see that docstring."""
        if not self._cycle_transcript_focus("shift+tab"):
            super().action_focus_previous()

    def _focus_ring(self) -> list[Composer | ChatMessage]:
        """Ordered focus targets: Composer, then messages newest-first.

        Textual's default Tab/Shift+Tab focus_next/focus_previous follow DOM
        mount order (oldest message first), which would make Tab-from-Composer
        land on the oldest message. This explicit ring makes Tab always move
        toward the most recent message first, matching the expected chat-review
        flow, while still wrapping cleanly at both ends.
        """
        composer = self.query_one("#composer", Composer)
        transcript = self.query_one("#transcript", Transcript)
        messages = list(reversed(transcript._messages))
        return [composer, *messages]

    def _cycle_transcript_focus(self, key: str) -> bool:
        """Move focus within the Composer/message ring. Returns True if handled.

        Only intervenes when the currently focused widget is Composer or a
        transcript ChatMessage — other focus targets (e.g. SessionPicker) fall
        back to Textual's default focus_next/focus_previous behavior.
        """
        ring = self._focus_ring()
        focused = self.focused
        if focused not in ring:
            return False
        index = ring.index(focused)
        index = (index + 1) % len(ring) if key == "tab" else (index - 1) % len(ring)
        self.set_focus(ring[index])
        return True

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
        if self._active_turn_worker is not None and self._active_turn_worker.is_running:
            self._active_turn_worker.cancel()
            self._clear_loading_message()
            self.query_one("#transcript", Transcript).add_message("system", "Turn cancelled.")
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
            console.print("Ctrl-C cancels a turn. Esc cancels a waiting turn or closes overlays. EOF exits. Shift+Enter inserts a newline.")
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
