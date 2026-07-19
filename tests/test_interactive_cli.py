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
