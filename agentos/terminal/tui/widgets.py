from __future__ import annotations

from textual.widgets import Input, ListView, Static


class Transcript(Static):
    DEFAULT_CSS = """
    Transcript {
        height: 1fr;
        padding: 1 2;
    }
    """


class Composer(Input):
    DEFAULT_CSS = """
    Composer {
        dock: bottom;
    }
    """


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
