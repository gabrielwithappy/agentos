import json
from pathlib import Path
from unittest import mock
from textwrap import dedent

from typer.testing import CliRunner

from agentos.cli import app

runner = CliRunner()


def test_root_without_tty_exits_2():
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Interactive mode requires a TTY" in result.stderr


def test_run_once_json_preserves_provider_event_names(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    result = runner.invoke(app, ["run", "--once", "hello", "--json", "--provider", "mock"])
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


def test_run_once_uses_saved_preferred_provider_when_flag_missing(tmp_path, monkeypatch):
    from agentos.terminal.paths import initialize_state, write_preferred_provider

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    initialize_state()
    write_preferred_provider("codex")

    result = runner.invoke(app, ["run", "--once", "hello", "--json"])

    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert events[0]["provider"] == "codex"


def test_run_once_explicit_provider_overrides_saved_preference(tmp_path, monkeypatch):
    from agentos.terminal.paths import initialize_state, write_preferred_provider

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    initialize_state()
    write_preferred_provider("codex")

    result = runner.invoke(app, ["run", "--once", "hello", "--json", "--provider", "mock"])

    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert events[0]["provider"] == "mock"


def write_fake_codex(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "codex"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import sys\n"
        f"{body}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_run_once_json_codex_preserves_event_schema(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"type": "item.completed", "item": {"type": "reasoning", "text": "Thinking"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Done"}}))
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))

    result = runner.invoke(app, ["run", "--once", "hello", "--json", "--provider", "codex-cli"])

    assert result.exit_code == 0
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert [event["type"] for event in events] == ["start", "reasoning", "message_delta", "done"]
    assert all("cli" in event.get("metadata", {}) for event in events)
    assert events[0]["provider"] == "codex-cli"


def test_run_once_json_codex_native_unauthenticated_response_has_no_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    result = runner.invoke(app, ["run", "--once", "hello", "--json", "--provider", "codex"])

    assert result.exit_code == 1
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert events[-1]["type"] == "error"
    assert "SENTINEL_SECRET" not in result.stdout
    assert "SENTINEL_SECRET" not in result.stderr


def test_run_once_json_codex_native_authenticated_stream_redacts_secret(tmp_path, monkeypatch):
    from agentos.llm.auth.openai_codex import TokenResult, persist_tokens
    from agentos.llm.auth.store import AuthFileStore
    from agentos.llm.transports.base import ProviderEvent

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    home = tmp_path / "home"
    store = AuthFileStore(home=home)
    persist_tokens(
        TokenResult(id_token="id", access_token="access-token-1", refresh_token="refresh-1", expires_in=3600),
        store=store,
    )

    class FakeTransport:
        def stream(self, request):
            yield ProviderEvent(type="start", response_id="resp_1")
            yield ProviderEvent(type="message_delta", text="token leaked: SENTINEL_SECRET", response_id="resp_1")
            yield ProviderEvent(type="done", response_id="resp_1", usage={"input_tokens": 1, "output_tokens": 2})

    import agentos.llm.providers.codex_native as codex_native_module

    original_init = codex_native_module.CodexNativeProvider.__init__

    def patched_init(self, *, store=None, transport_factory=None, model=codex_native_module.DEFAULT_MODEL):
        original_init(self, store=AuthFileStore(home=home), transport_factory=lambda token: FakeTransport(), model=model)

    monkeypatch.setattr(codex_native_module.CodexNativeProvider, "__init__", patched_init)

    result = runner.invoke(app, ["run", "--once", "hello", "--json", "--provider", "codex"])

    assert result.exit_code == 0
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert "SENTINEL_SECRET" not in result.stdout
    assert "SENTINEL_SECRET" not in result.stderr
