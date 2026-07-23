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
    SlashCommand("/login", "Codex login via the existing CLI account flow", "", "login"),
    SlashCommand("/status", "Show provider, session, hooks, last turn, and Codex auth status", "", "status"),
    SlashCommand("/logout", "Codex logout for the current CLI account session", "", "logout"),
    SlashCommand("/hotkeys", "Show all keyboard shortcuts", "", "hotkeys"),
    SlashCommand("/theme", "Switch the TUI colour theme", "[theme-name]", "theme"),
    SlashCommand("/session", "Show session command help", "[list|resume]", "session"),
    SlashCommand("/session list", "List recent sessions", "", "session_list"),
    SlashCommand("/session resume", "Open the session resume picker", "[session]", "session_resume"),
    SlashCommand("/hooks", "Show AgentOS-built hook status", "", "hooks"),
    SlashCommand("/tools", "Show tool calls from the last turn", "", "tools"),
    SlashCommand("/usage", "Show input/output usage from the last turn", "", "usage"),
    SlashCommand("/tree", "Show the current session's turn tree", "", "tree"),
    SlashCommand("/indicator", "Switch loading indicator style", "[ascii|unicode|emoji|kaomoji]", "indicator"),
    SlashCommand("/model", "Switch LLM provider for this session", "[provider]", "model"),
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
    exact_and_description = name_matches + description_matches
    try:
        from thefuzz import fuzz  # type: ignore[import-untyped]

        def _score(cmd: SlashCommand) -> int:
            name_score = fuzz.partial_ratio(normalized, cmd.name[1:].lower())
            desc_score = fuzz.partial_ratio(normalized, cmd.description.lower())
            return max(name_score, desc_score)

        return tuple(sorted(exact_and_description, key=_score, reverse=True))
    except ImportError:
        return tuple(exact_and_description)


def find_command(raw: str) -> SlashCommand | None:
    text = raw.strip()
    exact = next((command for command in COMMANDS if command.name == text), None)
    if exact is not None:
        return exact
    parts = text.split(maxsplit=1)
    if parts:
        return next((command for command in COMMANDS if command.name == parts[0]), None)
    return None
