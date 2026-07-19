import json
import os
from unittest import mock

from typer.testing import CliRunner

from agentos.cli import app
from agentos.llm.providers.mock import MOCK_MESSAGE, MockProvider
from agentos.llm.redaction import redact_text

runner = CliRunner()


def json_lines(output: str) -> list[dict]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_mock_provider_status_contract():
    payload = MockProvider().status().to_dict()

    assert payload["provider"] == "mock"
    assert payload["mode"] == "mock"
    assert payload["credential_present"] is False
    assert payload["authenticated"] is False
    assert payload["persistent_credential"] is False
    assert "No real account" in payload["message"]


def test_mock_provider_stream_events_are_deterministic():
    events = [event.to_dict() for event in MockProvider().stream_once("hello")]

    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert all(event["provider"] == "mock" for event in events)
    assert all(event["mode"] == "mock" for event in events)
    assert MOCK_MESSAGE in events[1]["text"]
    assert events[2]["usage"]["input_chars"] == 5


def test_redaction_replaces_sentinel_secret():
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        assert "SENTINEL_SECRET" not in redact_text("token=SENTINEL_SECRET")
        assert "[REDACTED]" in redact_text("token=SENTINEL_SECRET")


def test_llm_status_json_mock_contract():
    result = runner.invoke(app, ["llm", "status", "--json", "--provider", "mock"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "mock"
    assert payload["mode"] == "mock"
    assert payload["credential_present"] is False
    assert payload["authenticated"] is False
    assert payload["persistent_credential"] is False


def test_llm_login_logout_mock_contract():
    for action in ("login", "logout"):
        result = runner.invoke(app, ["llm", action, "--provider", "mock", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["action"] == action
        assert payload["provider"] == "mock"
        assert payload["mode"] == "mock"
        assert payload["authenticated"] is False
        assert payload["persistent_credential"] is False
        assert "No real account" in payload["message"]


def test_run_json_once_stream_events():
    result = runner.invoke(app, ["run", "--json", "--once", "hello"])

    assert result.exit_code == 0
    events = json_lines(result.stdout)
    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert all(event["provider"] == "mock" for event in events)
    assert all(event["mode"] == "mock" for event in events)


def test_unsupported_provider_jsonl_failure_schema():
    result = runner.invoke(app, ["run", "--json", "--once", "hello", "--provider", "unknown"])

    assert result.exit_code == 1
    events = json_lines(result.stdout)
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "error"
    assert event["provider"] == "unknown"
    assert event["mode"] == "unsupported"
    assert event["error"]["code"] == "unsupported_provider"
    assert "mock and codex providers" in event["error"]["message"]
    assert "--provider codex" in event["recovery"]
    assert "SENTINEL_SECRET" not in result.stdout
    assert "SENTINEL_SECRET" not in result.stderr


def test_secret_redaction_cli_surface():
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        commands = [
            ["llm", "status", "--json", "--provider", "mock"],
            ["llm", "login", "--json", "--provider", "mock"],
            ["llm", "logout", "--json", "--provider", "mock"],
            ["llm", "status", "--json", "--provider", "unknown"],
            ["run", "--json", "--once", "SENTINEL_SECRET"],
            ["run", "--json", "--once", "hello", "--provider", "unknown"],
        ]

        for command in commands:
            result = runner.invoke(app, command)
            assert "SENTINEL_SECRET" not in result.stdout
            assert "SENTINEL_SECRET" not in result.stderr
