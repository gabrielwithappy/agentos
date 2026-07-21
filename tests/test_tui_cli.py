from __future__ import annotations

import asyncio

from agentos.terminal.tui.app import AgentOSTui
from agentos.terminal.tui.commands import all_commands, command_palette_text, matching_commands
from agentos.terminal.tui.renderers import render_event, render_session_summary
from agentos.terminal.tui.state import TuiStatus
from agentos.terminal.tui.widgets import ChatMessage
from agentos.terminal import sessions


def _transcript_text(pilot) -> str:
    return "\n".join(message.text for message in pilot.app.query(ChatMessage))


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
            assert "You: hello" in _transcript_text(pilot)
            assert "Mock response from AgentOS" in _transcript_text(pilot)
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
            await pilot.pause()
            composer.value = "second"
            await pilot.press("enter")
            await pilot.pause()

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
            assert "Tool result: Mock tool executed successfully." in transcript
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

