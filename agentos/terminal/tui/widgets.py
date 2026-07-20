from __future__ import annotations

import re

from rich.markdown import Markdown
from textual.widgets import ListView, Static, OptionList, Label, TextArea
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical, VerticalScroll
from textual.app import ComposeResult
from textual.events import Key, Paste

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
        max-height: 14;
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
    """

    def __init__(self, prefix: str = "") -> None:
        super().__init__()
        self.prefix = prefix
        self.commands: tuple[SlashCommand, ...] = matching_commands(prefix)

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Label("AgentOS Commands", id="palette-title")
            yield OptionList(*self._labels(), id="palette-options")

    def _labels(self) -> list[str]:
        if not self.commands:
            return [f"No command matches {self.prefix!r}"]
        return [f"{command.name:<16} {command.description}" for command in self.commands]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.option_index < len(self.commands):
            self.dismiss(self.commands[event.option_index].name)

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss("")
            event.stop()


class ChatMessage(Static):
    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        margin-bottom: 1;
    }
    ChatMessage.user {
        padding: 0 1;
        border-left: tall $accent;
    }
    ChatMessage.assistant {
        padding: 0 1;
        border-left: tall $success;
    }
    ChatMessage.system {
        color: $text-muted;
    }
    """

    def __init__(self, role: str, text: str = "") -> None:
        super().__init__(text)
        self.role = role
        self.text = text
        self.rendered_as_markdown = False
        self.add_class(role)

    def update_text(self, text: str, *, markdown: bool = False) -> None:
        self.text = text
        if markdown and text.strip():
            self.rendered_as_markdown = True
            self.update(Markdown(text))
            return
        self.rendered_as_markdown = False
        self.update(text)


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

    def render(self) -> str:
        return "\n".join(
            self._format_message(message.role, message.text)
            for message in self._messages
            if message.text
        )

    def update(self, text: object = "") -> None:
        rendered = str(text)
        self._messages = [ChatMessage("system", rendered)] if rendered else []
        self.remove_children()
        for message in self._messages:
            self.mount(message)
        self._scroll_to_end()

    def add_message(self, role: str, text: str = "") -> ChatMessage:
        message = ChatMessage(role, text)
        self._messages.append(message)
        self.mount(message)
        self._scroll_to_end()
        return message

    def update_message(self, message: ChatMessage, text: str, *, markdown: bool = False) -> None:
        message.update_text(text, markdown=markdown)
        self._scroll_to_end()

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
        max-height: 10;
        min-height: 3;
    }
    """

    placeholder = "Type a message or / for commands"
    _paste_marker_pattern = re.compile(r"\[paste #(\d+)(?: (?:\+\d+ lines|\d+ chars))?\]")

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.kill_ring: list[str] = []
        self._last_action: str | None = None
        self._pastes: dict[int, str] = {}
        self._paste_counter = 0

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

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self.post_message(self.Submitted(self.submission_text, self))
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
