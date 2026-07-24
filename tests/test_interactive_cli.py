from typer.testing import CliRunner

from agentos.cli import app
from agentos.terminal import sessions
from agentos.terminal.paths import initialize_state

runner = CliRunner()


def test_session_list_show_delete_yes(tmp_path):
    initialize_state(tmp_path)
    sid = sessions.create_session(home=tmp_path)
    env = {"AGENTOS_HOME": str(tmp_path)}
    listed = runner.invoke(app, ["session", "list"], env=env)
    assert listed.exit_code == 0
    assert sid in listed.stdout
    shown = runner.invoke(app, ["session", "show", sid], env=env)
    assert shown.exit_code == 0
    deleted = runner.invoke(app, ["session", "delete", sid, "--yes"], env=env)
    assert deleted.exit_code == 0
    assert not (tmp_path / "sessions" / f"{sid}.jsonl").exists()


def test_session_delete_without_tty_and_yes_does_not_mutate(tmp_path):
    initialize_state(tmp_path)
    sid = sessions.create_session(home=tmp_path)
    result = runner.invoke(app, ["session", "delete", sid], env={"AGENTOS_HOME": str(tmp_path)})
    assert result.exit_code == 2
    assert "Confirmation requires a TTY" in result.stderr
    assert (tmp_path / "sessions" / f"{sid}.jsonl").exists()


def test_missing_session_recovery(tmp_path):
    initialize_state(tmp_path)
    result = runner.invoke(app, ["session", "show", "00000000-0000-0000-0000-000000000000"], env={"AGENTOS_HOME": str(tmp_path)})
    assert result.exit_code == 2
    assert "Next: agentos session list" in result.stderr


def test_malformed_session_events_recovery(tmp_path):
    initialize_state(tmp_path)
    sid = sessions.create_session(home=tmp_path)
    (tmp_path / "sessions" / f"{sid}.jsonl").write_text("{bad json\n", encoding="utf-8")
    result = runner.invoke(app, ["session", "show", sid], env={"AGENTOS_HOME": str(tmp_path)})
    assert result.exit_code == 2
    assert "Session events are malformed" in result.stderr


def test_prune_preview_uses_datetime_parsing(tmp_path):
    initialize_state(tmp_path)
    result = runner.invoke(app, ["session", "prune", "--before", "not-a-date", "--yes"], env={"AGENTOS_HOME": str(tmp_path)})
    assert result.exit_code == 2
    assert "Invalid isoformat" in result.stderr


def test_interactive_session_file_uses_cli_event_envelopes(tmp_path, monkeypatch):
    env = {"AGENTOS_HOME": str(tmp_path)}
    result = runner.invoke(app, ["run", "--once", "hello"], env=env)
    assert result.exit_code == 0


# ── PI session runtime Task 6 Step 2: legacy interactive fallback runtime wiring ──


def test_legacy_interactive_fallback_second_turn_carries_context_via_session_runtime(tmp_path, monkeypatch):
    """`run_interactive()` (used when the Textual TUI fails to start) now
    drives `ConversationRuntime.submit_turn()` too, not the stateless
    `stream_once(prompt)` shim — the mock provider's `stream_context()`
    echoes every prior `user` message, so a second turn in the same
    fallback session must see the first turn's text."""
    from agentos.terminal.interaction import run_interactive
    from agentos.terminal.paths import initialize_state

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    initialize_state()
    inputs = iter(["remember-marker-fallback", "second fallback turn", ""])

    def fake_input(_prompt: str = "") -> str:
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)

    printed: list[str] = []
    monkeypatch.setattr(
        "agentos.terminal.interaction.console.print",
        lambda text="", **kwargs: printed.append(str(text)),
    )

    exit_code = run_interactive(provider="mock")

    assert exit_code == 0
    joined = "\n".join(printed)
    second_response = joined.rsplit("Received context [", 1)[-1]
    assert "remember-marker-fallback" in second_response
    assert "second fallback turn" in second_response


def test_legacy_interactive_fallback_persists_conversation_runtime_snapshot(tmp_path, monkeypatch):
    from agentos.terminal.interaction import run_interactive
    from agentos.terminal.paths import initialize_state
    from agentos.terminal.sessions import conversation_snapshot_path, list_sessions

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    initialize_state()
    inputs = iter(["hello"])

    def fake_input(_prompt: str = "") -> str:
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("agentos.terminal.interaction.console.print", lambda *a, **k: None)

    run_interactive(provider="mock")

    rows = list_sessions()
    assert rows
    snapshot_path = conversation_snapshot_path(rows[0]["session_id"])
    assert snapshot_path.is_file()
