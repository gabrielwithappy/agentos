import json
from unittest import mock

from typer.testing import CliRunner

from agentos.cli import app

runner = CliRunner()


def test_root_without_tty_exits_2():
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Interactive mode requires a TTY" in result.stderr


def test_run_once_json_preserves_provider_event_names():
    result = runner.invoke(app, ["run", "--once", "hello", "--json"])
    assert result.exit_code == 0
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert [event["type"] for event in events] == [
        "start",
        "reasoning",
        "tool_call",
        "tool_result",
        "message_delta",
        "done",
    ]
    assert all("cli" in event.get("metadata", {}) for event in events)


def test_run_json_without_once_is_usage_error():
    result = runner.invoke(app, ["run", "--json", "hello"])
    assert result.exit_code == 2
    assert "--json requires --once" in result.stderr


def test_run_once_empty_prompt_is_usage_error():
    result = runner.invoke(app, ["run", "--once", "   ", "--json"])
    assert result.exit_code == 2
    assert "A prompt is required" in result.stderr


def test_unsupported_provider_json_emits_one_error():
    result = runner.invoke(app, ["run", "--once", "hello", "--provider", "bad", "--json"])
    assert result.exit_code == 1
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["error"]["code"] == "unsupported_provider"


def test_harness_requires_explicit_project_root():
    result = runner.invoke(app, ["harness"])
    assert result.exit_code == 2
    assert "Missing --project-root" in result.stderr


@mock.patch("agentos.commands.harness.os.execv")
def test_harness_uses_explicit_project_root(mock_execv):
    result = runner.invoke(app, ["harness", "--project-root", "."])
    assert result.exit_code == 0
    mock_execv.assert_called_once()
