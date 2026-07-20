from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlashCommand:
    name: str
    description: str
    argument_hint: str
    handler_id: str


COMMANDS: tuple[SlashCommand, ...] = (
    SlashCommand("/help", "Show commands and keyboard help", "", "help"),
    SlashCommand("/status", "Show provider, session, hooks, and last turn state", "", "status"),
    SlashCommand("/session", "Show session command help", "[list|resume]", "session"),
    SlashCommand("/session list", "List recent sessions", "", "session_list"),
    SlashCommand("/session resume", "Open the session resume picker", "[session]", "session_resume"),
    SlashCommand("/hooks", "Show AgentOS-built hook status", "", "hooks"),
    SlashCommand("/clear", "Clear the visible transcript", "", "clear"),
    SlashCommand("/exit", "Exit the TUI", "", "exit"),
)


def all_commands() -> tuple[SlashCommand, ...]:
    return COMMANDS


def command_palette_text() -> str:
    return "\n".join(
        f"{command.name} {command.argument_hint} - {command.description}".strip()
        for command in COMMANDS
    )


def matching_commands(prefix: str) -> tuple[SlashCommand, ...]:
    normalized = prefix.strip()
    if normalized.startswith("/"):
        normalized = normalized[1:]
    normalized = normalized.lower()
    if not normalized:
        return COMMANDS
    name_matches = [
        command
        for command in COMMANDS
        if normalized in command.name[1:].lower()
    ]
    description_matches = [
        command
        for command in COMMANDS
        if command not in name_matches
        and normalized in command.description.lower()
    ]
    return tuple(name_matches + description_matches)


def find_command(raw: str) -> SlashCommand | None:
    text = raw.strip()
    return next((command for command in COMMANDS if command.name == text), None)
