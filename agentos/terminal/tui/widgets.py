from __future__ import annotations

from textual.widgets import ListView, Static, OptionList, Label, TextArea
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.events import Key


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

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self.post_message(self.Submitted(self.text, self))
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
