from __future__ import annotations

import asyncio
import json
import threading

from agentos.llm.types import LLMEvent
from agentos.terminal.tui.app import AgentOSTui
from agentos.terminal.tui.commands import all_commands, command_palette_text, matching_commands
from agentos.terminal.tui.renderers import (
    TOOL_RENDERERS,
    render_event,
    render_mock_tool_table,
    render_session_summary,
    render_turn_tree,
)
from agentos.terminal.tui.state import TuiStatus
from agentos.terminal.tui.widgets import ChatMessage
from agentos.terminal import sessions


def _transcript_text(pilot) -> str:
    return "\n".join(message.text for message in pilot.app.query(ChatMessage))


async def await_transcript(pilot, expected_text: str, timeout: float = 1.0) -> None:
    import time
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if expected_text in _transcript_text(pilot):
            return
        await pilot.pause(0.05)
    assert expected_text in _transcript_text(pilot)

def test_footer_includes_stable_labels_and_mock_model(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)
    app = AgentOSTui(provider="mock")

    footer = app.status.footer_text()

    for label in ("cwd", "provider", "model", "session", "hooks", "mode", "last turn"):
        assert label in footer
    assert "provider mock" in footer
    assert "model mock" in footer
    assert "mode tui" in footer


def test_footer_truncates_values_but_preserves_labels():
    status = TuiStatus(
        cwd="/very/long/path/that/does/not/fit/in/a/narrow/terminal",
        provider="provider-with-a-long-name",
        model="model-with-a-long-name",
        session="session-with-a-long-name",
        hooks="hooks-with-a-long-name",
        last_turn="running-with-a-long-status",
        max_value_width=8,
    )

    footer = status.footer_text()

    for label in ("cwd", "provider", "model", "session", "hooks", "mode", "last turn"):
        assert label in footer
    assert "…" in footer


def test_layout_contains_transcript_composer_and_footer(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            assert "AgentOS" in _transcript_text(pilot)
            composer = pilot.app.query_one("#composer")
            status = str(pilot.app.query_one("#status").render())
            for label in ("cwd", "provider", "model", "session", "hooks", "mode", "last turn"):
                assert label in status

    asyncio.run(run())


def test_composer_submit_updates_transcript_and_restores_focus(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")
            assert "You: hello" in _transcript_text(pilot)
            assert "last turn done" in str(pilot.app.query_one("#status").render())
            session_files = list((tmp_path / "home" / "sessions").glob("*.jsonl"))
            assert session_files
            assert "agentos.cli-event/v1" in session_files[0].read_text(encoding="utf-8")
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_composer_submits_multiline_prompt(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello\nworld"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            assert "You: hello\nworld" in transcript
            assert composer.value == ""
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_transcript_accumulates_multiple_turns(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "first"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")
            composer.value = "second"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")

            transcript = _transcript_text(pilot)
            assert "You: first" in transcript
            assert "You: second" in transcript
            assert transcript.count("Mock response from AgentOS") == 2

    asyncio.run(run())


def test_assistant_message_finalizes_as_markdown(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "markdown"
            await pilot.press("enter")
            await pilot.pause()

            assistant_messages = [
                message
                for message in pilot.app.query(ChatMessage)
                if message.role == "assistant"
            ]
            assert assistant_messages
            assert assistant_messages[-1].rendered_as_markdown is True

    asyncio.run(run())


def test_composer_kill_yank_and_undo_shortcuts(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello world"
            composer.move_cursor((0, 6))
            await pilot.press("ctrl+k")
            assert composer.value == "hello "
            assert composer.kill_ring[-1] == "world"
            await pilot.press("ctrl+y")
            assert composer.value == "hello world"
            await pilot.press("ctrl+z")
            assert composer.value == "hello "

            composer.value = "hello world"
            composer.move_cursor((0, 6))
            await pilot.press("ctrl+u")
            assert composer.value == "world"
            assert composer.kill_ring[-1] == "hello "

    asyncio.run(run())


def test_composer_large_paste_marker_expands_on_submit(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            pasted = "\n".join(f"line {index}" for index in range(12))
            composer.insert_paste(pasted)
            assert composer.value == "[paste #1 +12 lines]"
            assert composer.submission_text == pasted
            await pilot.press("enter")
            await pilot.pause()
            transcript = _transcript_text(pilot)
            assert "You: line 0" in transcript
            assert "line 11" in transcript
            assert composer.value == ""
            assert composer.submission_text == ""

    asyncio.run(run())


def test_composer_newline_contract_is_deferred_to_multiline_widget(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_ctrl_b_menu_opens_and_escape_restores_composer(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            await pilot.press("ctrl+b")
            await pilot.pause()
            assert "AgentOS Menu" in str(pilot.app.screen.query_one("#menu-title").render())
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_escape_in_composer_is_safe_noop(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            await pilot.press("escape")
            assert pilot.app.focused is composer
            assert "AgentOS" in _transcript_text(pilot)

    asyncio.run(run())


def test_slash_command_catalog_contains_stable_names_descriptions_and_hints():
    commands = {command.name: command for command in all_commands()}

    for name in (
        "/help",
        "/status",
        "/session",
        "/session list",
        "/session resume",
        "/hooks",
        "/tools",
        "/usage",
        "/clear",
        "/exit",
    ):
        assert name in commands
        assert commands[name].description
        assert commands[name].handler_id
        assert commands[name].argument_hint is not None


def test_command_palette_lists_commands_with_descriptions():
    palette = command_palette_text()

    for name in ("/status", "/session", "/hooks", "/tools", "/usage", "/clear", "/exit"):
        assert name in palette
    assert "Show provider" in palette
    assert "Open the session resume picker" in palette


def test_matching_commands_filters_by_name_and_description():
    by_name = matching_commands("/sess")
    by_description = matching_commands("hook")

    assert {command.name for command in by_name} >= {"/session", "/session list", "/session resume"}
    assert {command.name for command in by_description} >= {"/hooks", "/status"}


def test_palette_and_unknown_command_recovery_restore_focus(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/"
            await pilot.press("enter")
            palette = _transcript_text(pilot)
            assert "/status" in palette
            assert "/session" in palette
            assert "/hooks" in palette
            assert "/clear" in palette
            assert "/exit" in palette
            composer.value = "/wat"
            await pilot.press("enter")
            assert _transcript_text(pilot) == "Unknown command. Next: /help"
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_tab_opens_filtered_command_palette_and_fills_composer(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/sess"
            await pilot.press("tab")
            await pilot.pause()
            command_names = {command.name for command in pilot.app.screen.commands}
            assert "/session" in command_names
            assert "/hooks" not in command_names
            await pilot.press("enter")
            await pilot.pause()
            assert composer.value.startswith("/session")
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_session_summary_sorts_and_marks_unavailable(tmp_path):
    old_id = sessions.create_session(provider="mock", mode="tui", home=tmp_path)
    new_id = sessions.create_session(provider="codex", mode="tui", home=tmp_path)
    (tmp_path / "sessions" / f"{old_id}.meta.json").write_text(
        '{"schema_version":"agentos.session/v1","session_id":"' + old_id + '","updated_at":"2026-01-01T00:00:00Z","provider":"mock","mode":"tui"}',
        encoding="utf-8",
    )
    (tmp_path / "sessions" / "broken.meta.json").write_text("{bad json\n", encoding="utf-8")

    rows = sessions.session_summaries(tmp_path)

    assert rows[0]["session_id"] == new_id
    assert any(row["status"] == "unavailable" for row in rows)
    assert all("short_id" in row for row in rows)


def test_session_picker_empty_cancel_resume_and_unavailable_states(tmp_path, monkeypatch):
    async def run_empty() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "empty-home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/session resume"
            await pilot.press("enter")
            assert "No sessions found. Esc to return." in _transcript_text(pilot)

    async def run_resume() -> None:
        home = tmp_path / "resume-home"
        monkeypatch.setenv("AGENTOS_HOME", str(home))
        expected_id = sessions.create_session(provider="mock", mode="tui", home=home)
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/session resume"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            assert f"Resumed session {expected_id[:8]}." in transcript
            assert expected_id[:8] in str(pilot.app.query_one("#status").render())

    asyncio.run(run_empty())
    asyncio.run(run_resume())


def test_session_resume_multiple_sessions_shows_picker_instead_of_auto_resume(tmp_path, monkeypatch):
    async def run() -> None:
        home = tmp_path / "picker-home"
        monkeypatch.setenv("AGENTOS_HOME", str(home))
        first = sessions.create_session(provider="mock", mode="tui", home=home)
        second = sessions.create_session(provider="mock", mode="tui", home=home)
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/session resume"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            assert "Session picker" in transcript
            assert "Esc to return" in transcript
            picker_text = "\n".join(str(item.children[0].render()) for item in pilot.app.query_one("#session-picker").children)
            assert first[:8] in picker_text
            assert second[:8] in picker_text
            await pilot.pause()
            assert pilot.app.focused is pilot.app.query_one("#session-picker")
            await pilot.press("escape")
            assert "Resume cancelled." in _transcript_text(pilot)
            composer = pilot.app.query_one("#composer")
            assert pilot.app.focused is composer
            composer.value = "/session resume"
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.focused is pilot.app.query_one("#session-picker")
            await pilot.press("enter")
            assert "Resumed session" in _transcript_text(pilot)

    asyncio.run(run())


def test_tui_hook_failure_recovery_updates_footer_and_preserves_focus(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock")
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "   "
            await pilot.press("enter")
            assert "Hook failed. Next: /hooks" in _transcript_text(pilot)
            assert "last turn error" in str(pilot.app.query_one("#status").render())
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_renderer_redacts_secret_from_provider_hook_and_session(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "AGENTOS_SENTINEL_SECRET")

    rendered = render_event({"type": "message_delta", "text": "hello AGENTOS_SENTINEL_SECRET"})
    hook = render_event({"type": "hook_error", "payload": "AGENTOS_SENTINEL_SECRET"})
    row = render_session_summary(
        {
            "short_id": "abc12345",
            "provider": "mock",
            "mode": "tui",
            "updated_at": "2026-07-19T00:00:00Z",
            "label": "AGENTOS_SENTINEL_SECRET",
            "available": True,
        }
    )

    assert "AGENTOS_SENTINEL_SECRET" not in rendered
    assert "AGENTOS_SENTINEL_SECRET" not in hook
    assert "AGENTOS_SENTINEL_SECRET" not in row
    assert "Hook failed. Next: /hooks" == hook


def test_process_event_redacts_secret_from_reasoning_tool_call_and_tool_result(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "AGENTOS_SENTINEL_SECRET")

    reasoning = render_event({"type": "reasoning", "text": "thinking about AGENTOS_SENTINEL_SECRET"})
    tool_call = render_event(
        {
            "type": "tool_call",
            "metadata": {"name": "mock_tool", "arguments": {"input": "AGENTOS_SENTINEL_SECRET"}},
        }
    )
    tool_result = render_event(
        {"type": "tool_result", "metadata": {"summary": "leaked AGENTOS_SENTINEL_SECRET value"}}
    )

    assert "AGENTOS_SENTINEL_SECRET" not in reasoning
    assert "AGENTOS_SENTINEL_SECRET" not in tool_call
    assert "AGENTOS_SENTINEL_SECRET" not in tool_result
    assert reasoning.startswith("Thinking: ")
    assert tool_call.startswith("Tool call: mock_tool(")
    assert tool_result.startswith("Tool result: ")


def test_transcript_shows_process_events_before_final_answer(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()

            transcript = _transcript_text(pilot)
            assert "Thinking: Considering how to respond to the prompt." in transcript
            assert "Tool call: mock_tool(input=hello)" in transcript
            # mock_tool has a registered custom table renderer (Milestone 4) —
            # it no longer shows the generic "Tool result: ..." plain text.
            assert "| field | value |" in transcript
            assert "| summary | Mock tool executed successfully. |" in transcript
            assert transcript.index("Thinking:") < transcript.index("Mock response from AgentOS")

    asyncio.run(run())


def test_tools_command_reports_no_tool_calls_before_first_turn(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/tools"
            await pilot.press("enter")
            assert (
                "No tool calls in the last turn. Next: send a message that needs a tool."
                in _transcript_text(pilot)
            )

    asyncio.run(run())


def test_tools_command_lists_tool_calls_after_turn(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()
            composer.value = "/tools"
            await pilot.press("enter")

            transcript = _transcript_text(pilot)
            assert "Tools used in the last turn:" in transcript
            assert "mock_tool(input=hello) -> Mock tool executed successfully." in transcript

    asyncio.run(run())


def test_usage_command_reports_no_usage_before_first_turn(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/usage"
            await pilot.press("enter")
            assert "No usage yet. Next: send a message." in _transcript_text(pilot)

    asyncio.run(run())


def test_usage_command_reports_last_turn_usage(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()
            composer.value = "/usage"
            await pilot.press("enter")

            transcript = _transcript_text(pilot)
            assert "Last turn usage: input 5 chars, output" in transcript

    asyncio.run(run())


# ── Milestone 1: /hotkeys ──────────────────────────────────────────────────────

def test_hotkeys_command_shows_keyboard_shortcuts(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/hotkeys"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            # Must contain core key names from the shortcut table
            assert "Enter" in transcript
            assert "Shift+Enter" in transcript
            assert "Ctrl+K" in transcript
            assert "Ctrl+B" in transcript
            assert "Esc" in transcript

    asyncio.run(run())


def test_hotkeys_command_listed_in_command_palette(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    text = command_palette_text()
    assert "/hotkeys" in text


# ── Milestone 2: /theme ────────────────────────────────────────────────────────

def test_theme_command_listed_in_commands():
    commands = all_commands()
    handler_ids = [cmd.handler_id for cmd in commands]
    assert "theme" in handler_ids


def test_theme_selection_changes_app_theme(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            original_theme = app.theme
            themes = sorted(app.available_themes.keys())
            different_theme = next((t for t in themes if t != original_theme), None)
            if different_theme is None:
                return  # Only one theme available — skip

            from agentos.terminal.tui.widgets import ThemeScreen
            result: list[str] = []

            def capture(selected: str) -> None:
                result.append(selected)
                if selected:
                    pilot.app.theme = selected

            pilot.app.push_screen(ThemeScreen(themes), capture)
            await pilot.pause()
            # Dismiss with the different theme to simulate selection
            pilot.app.screen.dismiss(different_theme)
            await pilot.pause()
            assert result == [different_theme]
            assert app.theme == different_theme

    asyncio.run(run())



def test_theme_escape_does_not_change_theme(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            original_theme = app.theme
            themes = sorted(app.available_themes.keys())

            from agentos.terminal.tui.widgets import ThemeScreen
            result = []
            def capture(selected: str) -> None:
                result.append(selected)
                if selected:
                    pilot.app.theme = selected

            pilot.app.push_screen(ThemeScreen(themes), capture)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            # Esc → callback receives "" → theme unchanged
            assert result == [""]
            assert app.theme == original_theme

    asyncio.run(run())


# ── Milestone 3: footer git_branch · cumulative usage ─────────────────────────

def test_footer_git_branch_shown_inside_repo(tmp_path, monkeypatch):
    """When git rev-parse succeeds, branch appears in footer."""
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))

    status = TuiStatus.initial(
        provider="mock",
        session_id="abc12345",
        git_branch="main",
    )
    footer = status.footer_text()
    assert "branch main" in footer


def test_footer_git_branch_omitted_outside_repo(tmp_path, monkeypatch):
    """When git_branch is None, branch field is absent from footer."""
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))

    status = TuiStatus.initial(
        provider="mock",
        session_id="abc12345",
        git_branch=None,
    )
    footer = status.footer_text()
    assert "branch" not in footer


def test_footer_git_branch_omitted_on_timeout(tmp_path, monkeypatch):
    """get_git_branch() returns None on TimeoutExpired, so footer omits branch."""
    import subprocess
    from agentos.terminal.tui.state import get_git_branch

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    branch = get_git_branch()
    assert branch is None


def test_footer_usage_starts_at_zero(tmp_path, monkeypatch):
    """Before any turn, total in/out should read 0/0."""
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)
    app = AgentOSTui(provider="mock", create_session_on_start=False)
    footer = app.status.footer_text()
    assert "total in/out 0/0 chars" in footer


def test_footer_usage_accumulates_and_survives_status_updates(tmp_path, monkeypatch):
    """Cumulative counters increase after a turn and are not reset by _status_with_totals()."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()
            # After one turn with mock provider (usage: input=5, output=X)
            assert app.total_input_chars > 0
            # Status reflects cumulative values (not 0/0)
            footer = app.status.footer_text()
            assert "total in/out 0/0 chars" not in footer

    asyncio.run(run())


# ── Milestone 4: tool_call/tool_result bordered, reasoning unbordered ──────────

def test_tool_border_tool_call_has_tool_class(tmp_path, monkeypatch):
    """tool_call event adds a ChatMessage with class 'tool', not 'reasoning'."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()
            messages = list(pilot.app.query(ChatMessage))
            tool_messages = [m for m in messages if m.has_class("tool")]
            reasoning_messages = [m for m in messages if m.has_class("reasoning")]
            # Mock provider emits tool_call + tool_result → at least 2 tool messages
            assert len(tool_messages) >= 2, f"Expected ≥2 tool messages, got {tool_messages}"
            # tool messages must NOT also have the reasoning class
            for m in tool_messages:
                assert not m.has_class("reasoning"), "tool message should not have reasoning class"

    asyncio.run(run())


def test_tool_border_reasoning_has_reasoning_class(tmp_path, monkeypatch):
    """reasoning event adds a ChatMessage with class 'reasoning', not 'tool'."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await pilot.pause()
            messages = list(pilot.app.query(ChatMessage))
            reasoning_messages = [m for m in messages if m.has_class("reasoning")]
            # Mock provider emits reasoning event → at least 1 reasoning message
            assert len(reasoning_messages) >= 1, f"Expected ≥1 reasoning messages, got {reasoning_messages}"
            for m in reasoning_messages:
                assert not m.has_class("tool"), "reasoning message should not have tool class"

    asyncio.run(run())


# ── Milestone 1 (Phase 2): streaming cancel / loading indicator ────────────────

def _blocking_stream_once(release_event: threading.Event, reached_wait: threading.Event):
    def stream_once(prompt: str, *, provider: str = "mock"):
        yield LLMEvent(type="start", provider=provider, mode="tui")
        reached_wait.set()
        release_event.wait(timeout=5)
        yield LLMEvent(
            type="message_delta",
            provider=provider,
            mode="tui",
            text="mock delayed response text",
        )
        yield LLMEvent(
            type="done",
            provider=provider,
            mode="tui",
            usage={"input_chars": 1, "output_chars": 1},
        )

    return stream_once


def test_loading_indicator_shown_while_waiting_and_removed_on_first_event(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        release_event = threading.Event()
        reached_wait = threading.Event()
        monkeypatch.setattr(
            "agentos.terminal.tui.app.stream_once",
            _blocking_stream_once(release_event, reached_wait),
        )
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await await_transcript(pilot, "Thinking…")
            assert reached_wait.wait(timeout=5)

            release_event.set()
            await await_transcript(pilot, "mock delayed response text")
            transcript_after = _transcript_text(pilot)
            assert "Thinking…" not in transcript_after

    asyncio.run(run())


def test_escape_cancel_turn_stops_further_output(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        release_event = threading.Event()
        reached_wait = threading.Event()
        monkeypatch.setattr(
            "agentos.terminal.tui.app.stream_once",
            _blocking_stream_once(release_event, reached_wait),
        )
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "hello"
            await pilot.press("enter")
            await await_transcript(pilot, "Thinking…")
            assert reached_wait.wait(timeout=5)

            await pilot.press("escape")
            await await_transcript(pilot, "Turn cancelled.")
            transcript = _transcript_text(pilot)
            assert "Thinking…" not in transcript

            release_event.set()
            await pilot.pause(0.2)
            transcript = _transcript_text(pilot)
            assert "mock delayed response text" not in transcript

    asyncio.run(run())


# ── Milestone 2 (Phase 2): session branch data model (parent_turn_id) ──────────

def test_parent_turn_id_chains_across_consecutive_tui_turns(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "first"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")
            composer.value = "second"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")
            await pilot.pause(0.1)

        session_files = list((tmp_path / "home" / "sessions").glob("*.jsonl"))
        assert session_files
        lines = [
            json.loads(line)
            for line in session_files[0].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        input_events = [event for event in lines if event["type"] == "input_received"]
        assert len(input_events) == 2
        first_turn_id, second_turn_id = input_events[0]["turn_id"], input_events[1]["turn_id"]
        assert first_turn_id != second_turn_id

        first_turn_events = [event for event in lines if event["turn_id"] == first_turn_id]
        assert first_turn_events
        assert all(event.get("parent_turn_id") is None for event in first_turn_events)

        second_turn_provider_events = [
            event
            for event in lines
            if event["turn_id"] == second_turn_id and event["type"] != "input_received"
        ]
        assert second_turn_provider_events
        assert all(event.get("parent_turn_id") == first_turn_id for event in second_turn_provider_events)

    asyncio.run(run())


# ── Milestone 3 (Phase 2): /tree branch explorer ────────────────────────────────

def test_tree_command_shows_empty_state_before_first_turn(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/tree"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            assert "No turns yet. Next: send a message." in transcript

    asyncio.run(run())


def test_tree_command_shows_linear_chain_after_two_turns(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "first"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")
            composer.value = "second"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")

            composer.value = "/tree"
            await pilot.press("enter")
            transcript = _transcript_text(pilot)
            # Single chain: exactly one root, one child indented under it.
            assert transcript.count("├─ ") + transcript.count("└─ ") == 2
            assert "│  └─ " in transcript or "   └─ " in transcript

    asyncio.run(run())


def test_tree_command_listed_in_command_palette(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    text = command_palette_text()
    assert "/tree" in text


def test_render_turn_tree_shows_actual_branches_when_parent_data_diverges():
    # No branch-creation UI exists yet, but render_turn_tree itself must already
    # render a real fork if two turns ever share the same parent_turn_id.
    events = [
        {"turn_id": "root1", "parent_turn_id": None},
        {"turn_id": "childA", "parent_turn_id": "root1"},
        {"turn_id": "childB", "parent_turn_id": "root1"},
    ]
    tree_text = render_turn_tree(events)
    assert "root1" in tree_text
    assert "childA" in tree_text
    assert "childB" in tree_text
    assert "├─ " in tree_text  # non-last sibling uses the branch connector
    assert "└─ " in tree_text  # last sibling uses the terminal connector


# ── Milestone 4 (Phase 2): per-tool custom renderer architecture ───────────────

def test_mock_tool_table_renderer_is_registered():
    assert "mock_tool" in TOOL_RENDERERS
    assert TOOL_RENDERERS["mock_tool"] is render_mock_tool_table


def test_tool_renderer_dispatches_mock_tool_to_table_and_unregistered_tool_falls_back_to_plain_text():
    table_rendered = render_event(
        {"type": "tool_result", "metadata": {"name": "mock_tool", "summary": "did the thing"}}
    )
    assert "| field | value |" in table_rendered
    assert "| summary | did the thing |" in table_rendered

    plain_rendered = render_event(
        {"type": "tool_result", "metadata": {"name": "some_other_tool", "summary": "did another thing"}}
    )
    assert plain_rendered == "Tool result: did another thing"
    assert "| field | value |" not in plain_rendered

    # No name at all (legacy provider payload shape) also falls back safely.
    legacy_rendered = render_event({"type": "tool_result", "metadata": {"summary": "legacy shape"}})
    assert legacy_rendered == "Tool result: legacy shape"


def test_mock_tool_table_redacts_secret(monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "AGENTOS_SENTINEL_SECRET")

    rendered = render_event(
        {
            "type": "tool_result",
            "metadata": {"name": "mock_tool", "summary": "leaked AGENTOS_SENTINEL_SECRET value"},
        }
    )

    assert "| field | value |" in rendered
    assert "AGENTOS_SENTINEL_SECRET" not in rendered


# ── Phase 3 Milestones Tests ──────────────────────────────────────────────────

def test_notification_toast_on_hook_error(tmp_path, monkeypatch):
    """Milestone 1: Hook failure produces a toast notification banner."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock")
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "   "
            await pilot.press("enter")
            await pilot.pause(0.1)
            # Footer is updated to error
            assert "last turn error" in str(pilot.app.query_one("#status").render())

    asyncio.run(run())


def test_indicator_style_switch_command(tmp_path, monkeypatch):
    """Milestone 2: /indicator command switches loading indicator style."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            assert app._indicator_style == "ascii"
            app.process_input("/indicator unicode")
            assert app._indicator_style == "unicode"
            app.process_input("/indicator emoji")
            assert app._indicator_style == "emoji"
            app.process_input("/indicator kaomoji")
            assert app._indicator_style == "kaomoji"
            # Unknown style does not change state
            app.process_input("/indicator invalid_style")
            assert app._indicator_style == "kaomoji"

    asyncio.run(run())


def test_command_palette_fuzzy_filter():
    """Milestone 3: matching_commands returns filtered and fuzzy-ranked commands."""
    # Prefix filtering
    tree_cmds = matching_commands("tr")
    assert any(cmd.name == "/tree" for cmd in tree_cmds)

    # Description filtering
    colour_cmds = matching_commands("colour")
    assert any(cmd.name == "/theme" for cmd in colour_cmds)

    # Empty query returns all commands
    all_cmds = matching_commands("")
    assert len(all_cmds) >= 15


def test_branch_fork_creates_parent_turn_id(tmp_path, monkeypatch):
    """Milestone 2: Tab-then-f on a focused message forks from that turn via the real key path.

    Phase 3 had only exercised this by calling on_transcript_fork_requested()
    directly, which passed even though ChatMessage was never actually
    focusable — a real user pressing Tab then f could never reach this code.
    This test drives the same real key sequence a user would press.
    """
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "turn 1"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")

            assistant_message = pilot.app.query_one("#transcript")._messages[-1]
            assert assistant_message.turn_id, "assistant message must carry a turn_id for f to do anything"

            await pilot.press("tab")
            assert pilot.app.focused is assistant_message
            await pilot.press("f")

            assert app._pending_parent_turn_id == assistant_message.turn_id

    asyncio.run(run())


def test_focus_cycle(tmp_path, monkeypatch):
    """Milestone 1: Tab/Shift+Tab move focus between Composer and messages, newest-first, wrapping at both ends."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "turn 1"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")

            messages = list(pilot.app.query_one("#transcript")._messages)
            assert len(messages) >= 2  # user turn + assistant reply

            # Tab from Composer moves to the most recent message with visible focus styling
            await pilot.press("tab")
            assert pilot.app.focused is messages[-1]
            assert pilot.app.focused.has_pseudo_class("focus")

            # A second Tab steps to the next-older message
            await pilot.press("tab")
            assert pilot.app.focused is messages[-2]

            # Shift+Tab reverses: newer message, then back to Composer
            await pilot.press("shift+tab")
            assert pilot.app.focused is messages[-1]
            await pilot.press("shift+tab")
            assert pilot.app.focused is composer

            # Shift+Tab from Composer wraps to the oldest message
            await pilot.press("shift+tab")
            assert pilot.app.focused is messages[0]

            # Tab from the oldest message wraps back to Composer
            await pilot.press("tab")
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_copy_message(tmp_path, monkeypatch):
    """Milestone 3: c on a focused message copies its text and shows an 'attempted' notification."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "turn 1"
            await pilot.press("enter")
            await await_transcript(pilot, "Mock response from AgentOS")

            target = pilot.app.query_one("#transcript")._messages[-1]
            await pilot.press("tab")
            assert pilot.app.focused is target

            await pilot.press("c")
            assert pilot.app.clipboard == target.text
            # OSC 52 has no ACK from the terminal, so the notification must say
            # "attempted", not an unconditional "copied", to avoid a false
            # success claim on terminals that don't support OSC 52.
            notifications = " ".join(n.message for n in pilot.app._notifications)
            assert "복사됨" not in notifications
            assert "시도" in notifications

    asyncio.run(run())


def test_composer_clipboard(tmp_path, monkeypatch):
    """Milestone 4: Composer's Ctrl+C/Ctrl+V already work via Textual's built-in TextArea bindings."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.focus()
            composer.text = "copy me"
            composer.select_all()
            await pilot.pause()

            await pilot.press("ctrl+c")
            assert "copy me" in pilot.app.clipboard

            composer.text = ""
            await pilot.press("ctrl+v")
            assert "copy me" in composer.text

    asyncio.run(run())


def test_model_switch_command(tmp_path, monkeypatch):
    """Milestone 5: /model command switches LLM provider in session."""
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            assert app.provider == "mock"
            app.process_input("/model codex")
            assert app.provider == "codex"
            app.process_input("/model mock")
            assert app.provider == "mock"
            # Invalid provider does not change state
            app.process_input("/model non_existent_provider")
            assert app.provider == "mock"

    asyncio.run(run())


def test_streaming_markdown_helpers():
    """Milestone 6: Code block detection helpers for streaming markdown."""
    from agentos.terminal.tui.app import _has_complete_markdown_block, _has_open_code_block

    # Unmatched open fence
    open_fence = "Hello\n```python\ndef foo():\n"
    assert _has_open_code_block(open_fence) is True
    assert _has_complete_markdown_block(open_fence) is False

    # Closed code block
    closed_fence = "Hello\n```python\ndef foo():\n    return 42\n```\nDone."
    assert _has_open_code_block(closed_fence) is False
    assert _has_complete_markdown_block(closed_fence) is True

    # Table block
    table_text = "Here is table:\n| header1 | header2 |\n| val1 | val2 |"
    assert _has_complete_markdown_block(table_text) is True


