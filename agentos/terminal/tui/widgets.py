from __future__ import annotations

import re

from rich.markdown import Markdown
from textual.timer import Timer
from textual.widgets import ListView, Static, OptionList, Label, TextArea, Input
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical, VerticalScroll
from textual.app import ComposeResult
from textual.events import Key, Paste
from textual.reactive import reactive

from agentos.terminal.tui.commands import SlashCommand, matching_commands


class MenuScreen(ModalScreen[str]):
    DEFAULT_CSS = """
    MenuScreen {
        align: center middle;
    }
    #menu-container {
        width: 50;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    #menu-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-container"):
            yield Label("AgentOS Menu", id="menu-title")
            yield OptionList(
                "Resume Session",
                "List Sessions",
                "Show Hooks",
                "Help",
                "Exit",
                id="menu-options",
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        commands = ["/session resume", "/session list", "/hooks", "/help", "/exit"]
        if 0 <= event.option_index < len(commands):
            self.dismiss(commands[event.option_index])

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss("")
            event.stop()


class CommandPaletteScreen(ModalScreen[str]):
    DEFAULT_CSS = """
    CommandPaletteScreen {
        align: center middle;
    }
    #palette-container {
        width: 72;
        max-width: 90%;
        height: auto;
        max-height: 18;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    #palette-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    #palette-search {
        margin-bottom: 1;
        border: round $accent-darken-2;
    }
    """

    def __init__(self, prefix: str = "") -> None:
        super().__init__()
        self.prefix = prefix
        self.commands: tuple[SlashCommand, ...] = matching_commands(prefix)

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Label("AgentOS Commands  (type to filter, Enter to select, Esc to cancel)", id="palette-title")
            yield Input(value=self.prefix.lstrip("/"), placeholder="Filter commands…", id="palette-search")
            yield OptionList(*self._labels(), id="palette-options")

    def on_mount(self) -> None:
        self.query_one("#palette-search", Input).focus()

    def _labels(self) -> list[str]:
        if not self.commands:
            return ["No matching commands"]
        return [f"{command.name:<16} {command.description}" for command in self.commands]

    def _refresh_list(self, query: str) -> None:
        self.commands = matching_commands(query)
        option_list = self.query_one("#palette-options", OptionList)
        option_list.clear_options()
        for label in self._labels():
            option_list.add_option(label)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter in search box selects the first matching command."""
        if self.commands:
            self.dismiss(self.commands[0].name)
        event.stop()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.option_index < len(self.commands):
            self.dismiss(self.commands[event.option_index].name)

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss("")
            event.stop()


class ThemeScreen(ModalScreen[str]):
    DEFAULT_CSS = """
    ThemeScreen {
        align: center middle;
    }
    #theme-container {
        width: 50;
        height: auto;
        max-height: 24;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    #theme-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    """

    def __init__(self, themes: list[str]) -> None:
        super().__init__()
        self._themes = themes

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-container"):
            yield Label("Select Theme (Esc to cancel)", id="theme-title")
            yield OptionList(*self._themes, id="theme-options")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.option_index < len(self._themes):
            self.dismiss(self._themes[event.option_index])

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss("")
            event.stop()


class ChatMessage(Static):
    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        margin-bottom: 1;
        padding: 0;
    }
    ChatMessage.user {
        color: $success;
    }
    ChatMessage.assistant {
    }
    ChatMessage.system {
        color: $text-muted;
    }
    ChatMessage.reasoning {
        color: $text-muted;
        padding-left: 1;
        margin-bottom: 0;
    }
    ChatMessage.tool {
        color: $warning;
        padding-left: 1;
        margin-bottom: 0;
        border: round $warning;
    }
    ChatMessage.loading {
        color: $text-muted;
        padding-left: 1;
        margin-bottom: 0;
    }
    """

    def __init__(self, role: str, text: str = "", turn_id: str | None = None) -> None:
        super().__init__(text)
        self.role = role
        self.text = text
        self.turn_id = turn_id
        self.rendered_as_markdown = False
        self.add_class(role)

    class ForkRequested(Message):
        """Posted when the user requests a fork from this message's turn."""

        def __init__(self, chat_message: ChatMessage) -> None:
            super().__init__()
            self.chat_message = chat_message

    def action_fork_from_here(self) -> None:
        """Triggered by 'f' key — request a fork from this turn."""
        if self.turn_id:
            self.post_message(self.ForkRequested(self))

    def on_key(self, event: Key) -> None:
        if event.key == "f" and self.turn_id:
            self.action_fork_from_here()
            event.stop()

    def update_text(self, text: str, *, markdown: bool = False) -> None:
        self.text = text
        if markdown and text.strip():
            self.rendered_as_markdown = True
            self.update(Markdown(text))
            return
        self.rendered_as_markdown = False
        self.update(text)


# Spinner frame sets for each style
_SPINNER_FRAMES: dict[str, tuple[str, ...]] = {
    "ascii": ("|", "/", "-", "\\"),
    "unicode": ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"),
    "emoji": ("⚕️", "🌀", "🤔", "✨"),
    "kaomoji": ("(・・;)", "(；・∀・)", "(￣ー￣；)", "(・_・;)"),
}


class SpinnerMessage(ChatMessage):
    """Animated loading indicator that cycles through style frames."""

    DEFAULT_CSS = """
    SpinnerMessage {
        color: $text-muted;
        padding-left: 1;
        margin-bottom: 0;
    }
    """

    _frame_index: reactive[int] = reactive(0)

    def __init__(self, style: str = "ascii", turn_id: str | None = None) -> None:
        super().__init__("loading", "Thinking…", turn_id=turn_id)
        self._style = style
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.12, self._tick)

    def on_unmount(self) -> None:
        if self._timer is not None:
            self._timer.stop()

    def _format_frame(self, frame: str) -> str:
        return f"{frame} Thinking…"

    def _tick(self) -> None:
        frames = _SPINNER_FRAMES.get(self._style, _SPINNER_FRAMES["ascii"])
        self._frame_index = (self._frame_index + 1) % len(frames)
        self.text = self._format_frame(frames[self._frame_index])
        self.update(self.text)

    def set_style(self, style: str) -> None:
        self._style = style
        self._frame_index = 0
        frames = _SPINNER_FRAMES.get(style, _SPINNER_FRAMES["ascii"])
        self.text = self._format_frame(frames[0])
        self.update(self.text)


class Transcript(VerticalScroll):
    DEFAULT_CSS = """
    Transcript {
        height: 1fr;
        padding: 1 2;
    }
    """

    def __init__(self, initial_text: str = "", **kwargs: object) -> None:
        children = [ChatMessage("system", initial_text)] if initial_text else []
        self._messages: list[ChatMessage] = children.copy()
        kwargs.setdefault("can_focus", False)
        super().__init__(*children, **kwargs)

    class ForkRequested(Message):
        """Bubbled up from ChatMessage — carries the turn_id to fork from."""

        def __init__(self, turn_id: str) -> None:
            super().__init__()
            self.turn_id = turn_id

    def on_chat_message_fork_requested(self, event: ChatMessage.ForkRequested) -> None:
        """Relay fork request up to the app with the resolved turn_id."""
        if event.chat_message.turn_id:
            event.stop()
            self.post_message(self.ForkRequested(event.chat_message.turn_id))

    def update(self, text: object = "") -> None:
        rendered = str(text)
        self._messages = [ChatMessage("system", rendered)] if rendered else []
        self.remove_children()
        for message in self._messages:
            self.mount(message)
        self._scroll_to_end()

    def add_message(self, role: str, text: str = "", *, turn_id: str | None = None, style: str = "ascii") -> ChatMessage:
        if role in ("spinner", "loading"):
            message = SpinnerMessage(style=style, turn_id=turn_id)
        else:
            message = ChatMessage(role, self._format_message(role, text), turn_id=turn_id)
        self._messages.append(message)
        self.mount(message)
        self._scroll_to_end()
        return message

    def update_message(self, message: ChatMessage, text: str, *, markdown: bool = False) -> None:
        message.update_text(text, markdown=markdown)
        self._scroll_to_end()

    def remove_message(self, message: ChatMessage) -> None:
        if message in self._messages:
            self._messages.remove(message)
            if message.is_mounted:
                message.remove()


    def _format_message(self, role: str, text: str) -> str:
        if role == "user":
            return f"You: {text}"
        if role == "assistant":
            return text
        return text

    def _scroll_to_end(self) -> None:
        if self.is_mounted:
            self.scroll_end(animate=False)


class Composer(TextArea):
    DEFAULT_CSS = """
    Composer {
        dock: bottom;
        height: auto;
        max-height: 15;
        min-height: 3;
        border: round $accent;
        padding: 0 1;
        margin: 1 2;
    }
    """

    _paste_marker_pattern = re.compile(r"\[paste #(\d+)(?: (?:\+\d+ lines|\d+ chars))?\]")

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.kill_ring: list[str] = []
        self._last_action: str | None = None
        self._pastes: dict[int, str] = {}
        self._paste_counter = 0
        self.prompt_history: list[str] = []
        self.history_index: int = 0
        self.temp_buffer: str = ""

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, text: str) -> None:
        self.text = text

    @property
    def submission_text(self) -> str:
        return self.expand_paste_markers(self.text)

    def reset_editor_state(self) -> None:
        self.text = ""
        self._pastes.clear()
        self._paste_counter = 0
        self._last_action = None

    class Submitted(Message):
        def __init__(self, value: str, input: Composer) -> None:
            super().__init__()
            self.value = value
            self.input = input

    class CompletionRequested(Message):
        def __init__(self, value: str, input: Composer) -> None:
            super().__init__()
            self.value = value
            self.input = input

    def save_to_history(self, text: str) -> None:
        if not text.strip():
            return
        if not self.prompt_history or self.prompt_history[-1] != text:
            self.prompt_history.append(text)
        self.history_index = len(self.prompt_history)
        self.temp_buffer = ""

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            event.stop()
            self.post_message(self.Submitted(self.submission_text, self))
            try:
                self.save_to_history(self.submission_text)
            except Exception:
                pass
        elif event.key == "shift+enter":
            self.insert("\n")
            event.stop()
        elif event.key == "up" and self.cursor_location == (0, 0):
            if self.history_index > 0:
                if self.history_index == len(self.prompt_history):
                    self.temp_buffer = self.text
                self.history_index -= 1
                self.text = self.prompt_history[self.history_index]
                self.action_cursor_line_end()
            event.stop()
        elif event.key == "down":
            last_line = self.document.line_count - 1
            if self.cursor_location == (last_line, len(self.document.get_line(last_line))):
                if self.history_index < len(self.prompt_history):
                    self.history_index += 1
                    if self.history_index == len(self.prompt_history):
                        self.text = self.temp_buffer
                    else:
                        self.text = self.prompt_history[self.history_index]
                    self.action_cursor_line_end()
                event.stop()
        elif event.key == "ctrl+z":
            self.action_undo()
            self._last_action = None
            event.stop()
        elif event.key == "ctrl+k":
            self.kill_to_end_of_line()
            event.stop()
        elif event.key == "ctrl+u":
            self.kill_to_start_of_line()
            event.stop()
        elif event.key in {"alt+backspace", "ctrl+w"}:
            self.kill_word_left()
            event.stop()
        elif event.key == "ctrl+y":
            self.yank()
            event.stop()
        elif event.key == "tab" and self.text.lstrip().startswith("/"):
            self.post_message(self.CompletionRequested(self.text, self))
            event.stop()

    def on_paste(self, event: Paste) -> None:
        self.insert_paste(event.text)
        event.stop()

    def insert_paste(self, pasted_text: str) -> None:
        normalized = self._normalize_paste(pasted_text)
        if not normalized:
            return
        lines = normalized.split("\n")
        marker = ""
        if len(lines) > 10:
            marker = self._store_paste(normalized, f"+{len(lines)} lines")
        elif len(normalized) > 1000:
            marker = self._store_paste(normalized, f"{len(normalized)} chars")
        self.insert(marker or normalized)
        self._last_action = None

    def expand_paste_markers(self, text: str) -> str:
        def replacement(match: re.Match[str]) -> str:
            paste_id = int(match.group(1))
            return self._pastes.get(paste_id, match.group(0))

        return self._paste_marker_pattern.sub(replacement, text)

    def kill_to_end_of_line(self) -> None:
        start = self.selection.end
        end = self.get_cursor_line_end_location()
        deleted = self.get_text_range(start, end)
        if not deleted and not self.cursor_at_end_of_text:
            end = self.get_cursor_right_location()
            deleted = self.get_text_range(start, end)
        self._kill_range(start, end, deleted, prepend=False)

    def kill_to_start_of_line(self) -> None:
        start = self.get_cursor_line_start_location()
        end = self.selection.end
        deleted = self.get_text_range(start, end)
        if not deleted and not self.cursor_at_start_of_text:
            start = self.get_cursor_left_location()
            deleted = self.get_text_range(start, end)
        self._kill_range(start, end, deleted, prepend=True)

    def kill_word_left(self) -> None:
        if self.cursor_at_start_of_text:
            return
        start = self.get_cursor_word_left_location()
        end = self.selection.end
        deleted = self.get_text_range(start, end)
        self._kill_range(start, end, deleted, prepend=True)

    def yank(self) -> None:
        if not self.kill_ring:
            return
        self.insert(self.kill_ring[-1])
        self._last_action = "yank"

    def _kill_range(self, start: tuple[int, int], end: tuple[int, int], deleted: str, *, prepend: bool) -> None:
        if not deleted:
            return
        if self._last_action == "kill" and self.kill_ring:
            if prepend:
                self.kill_ring[-1] = deleted + self.kill_ring[-1]
            else:
                self.kill_ring[-1] += deleted
        else:
            self.kill_ring.append(deleted)
        self.delete(start, end, maintain_selection_offset=False)
        self._last_action = "kill"

    def _store_paste(self, text: str, suffix: str) -> str:
        self._paste_counter += 1
        paste_id = self._paste_counter
        self._pastes[paste_id] = text
        return f"[paste #{paste_id} {suffix}]"

    def _normalize_paste(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
        return "".join(char for char in normalized if char == "\n" or ord(char) >= 32)


class StatusFooter(Static):
    DEFAULT_CSS = """
    StatusFooter {
        dock: bottom;
        height: 1;
    }
    """


class SessionPicker(ListView):
    DEFAULT_CSS = """
    SessionPicker {
        height: auto;
        max-height: 8;
    }
    """
