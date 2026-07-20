from __future__ import annotations

import asyncio

from agentos.terminal.tui.app import AgentOSTui
from agentos.terminal.tui.commands import all_commands, command_palette_text, matching_commands
from agentos.terminal.tui.renderers import render_event, render_session_summary
from agentos.terminal.tui.state import TuiStatus
from agentos.terminal import sessions


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
            assert "AgentOS" in str(pilot.app.query_one("#transcript").render())
            composer = pilot.app.query_one("#composer")
            assert composer.placeholder == "Type a message or / for commands"
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
            assert "You: hello" in str(pilot.app.query_one("#transcript").render())
            assert "Mock response from AgentOS" in str(pilot.app.query_one("#transcript").render())
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
            transcript = str(pilot.app.query_one("#transcript").render())
            assert "You: hello\nworld" in transcript
            assert composer.value == ""
            assert pilot.app.focused is composer

    asyncio.run(run())


def test_composer_newline_contract_is_deferred_to_multiline_widget(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            assert composer.placeholder == "Type a message or / for commands"
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
            assert "AgentOS" in str(pilot.app.query_one("#transcript").render())

    asyncio.run(run())


def test_slash_command_catalog_contains_stable_names_descriptions_and_hints():
    commands = {command.name: command for command in all_commands()}

    for name in ("/help", "/status", "/session", "/session list", "/session resume", "/hooks", "/clear", "/exit"):
        assert name in commands
        assert commands[name].description
        assert commands[name].handler_id
        assert commands[name].argument_hint is not None


def test_command_palette_lists_commands_with_descriptions():
    palette = command_palette_text()

    for name in ("/status", "/session", "/hooks", "/clear", "/exit"):
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
            palette = str(pilot.app.query_one("#transcript").render())
            assert "/status" in palette
            assert "/session" in palette
            assert "/hooks" in palette
            assert "/clear" in palette
            assert "/exit" in palette
            composer.value = "/wat"
            await pilot.press("enter")
            assert str(pilot.app.query_one("#transcript").render()) == "Unknown command. Next: /help"
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
            assert "No sessions found. Esc to return." in str(pilot.app.query_one("#transcript").render())

    async def run_resume() -> None:
        home = tmp_path / "resume-home"
        monkeypatch.setenv("AGENTOS_HOME", str(home))
        expected_id = sessions.create_session(provider="mock", mode="tui", home=home)
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "/session resume"
            await pilot.press("enter")
            transcript = str(pilot.app.query_one("#transcript").render())
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
            transcript = str(pilot.app.query_one("#transcript").render())
            assert "Session picker" in transcript
            assert "Esc to return" in transcript
            picker_text = "\n".join(str(item.children[0].render()) for item in pilot.app.query_one("#session-picker").children)
            assert first[:8] in picker_text
            assert second[:8] in picker_text
            await pilot.pause()
            assert pilot.app.focused is pilot.app.query_one("#session-picker")
            await pilot.press("escape")
            assert "Resume cancelled." in str(pilot.app.query_one("#transcript").render())
            composer = pilot.app.query_one("#composer")
            assert pilot.app.focused is composer
            composer.value = "/session resume"
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.focused is pilot.app.query_one("#session-picker")
            await pilot.press("enter")
            assert "Resumed session" in str(pilot.app.query_one("#transcript").render())

    asyncio.run(run())


def test_tui_hook_failure_recovery_updates_footer_and_preserves_focus(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock")
        async with app.run_test() as pilot:
            composer = pilot.app.query_one("#composer")
            composer.value = "   "
            await pilot.press("enter")
            assert "Hook failed. Next: /hooks" in str(pilot.app.query_one("#transcript").render())
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
