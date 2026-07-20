from __future__ import annotations

from textual.widgets import ListView, Static, OptionList, Label, TextArea
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.events import Key

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


class Transcript(Static):
    DEFAULT_CSS = """
    Transcript {
        height: 1fr;
        padding: 1 2;
    }
    """


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

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, text: str) -> None:
        self.text = text

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
            self.post_message(self.Submitted(self.text, self))
            event.stop()
        elif event.key == "tab" and self.text.lstrip().startswith("/"):
            self.post_message(self.CompletionRequested(self.text, self))
            event.stop()


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
