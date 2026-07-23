import json
import os
import time
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from agentos.cli import app
from agentos.llm.providers.codex_cli import CodexCliProvider


runner = CliRunner()


def json_lines(output: str) -> list[dict]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def write_fake_codex(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "codex"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        f"{body}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_executable_discovery_uses_codex_cli_path(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:] == ["login", "status"]:
                print("signed in")
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    status = CodexCliProvider().status()

    assert status.status == "authenticated"
    assert status.authenticated is True


def test_subprocess_env_does_not_forward_test_sentinel(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if os.environ.get("AGENTOS_TEST_SECRET"):
                raise SystemExit(9)
            if sys.argv[1:] == ["login", "status"]:
                print("signed in")
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    assert CodexCliProvider().status().status == "authenticated"


def test_status_missing_cli_contract(monkeypatch):
    monkeypatch.setenv("CODEX_CLI_PATH", "/missing/codex")

    payload = CodexCliProvider().status().to_dict()

    assert payload["provider"] == "codex"
    assert payload["mode"] == "account-login"
    assert payload["status"] == "missing_cli"
    assert payload["credential_present"] is False
    assert payload["authenticated"] is False
    assert payload["persistent_credential"] is False
    assert payload["next_command"] == "codex login"
    assert "Install Codex CLI" in payload["recovery"]
    assert "/missing/codex" not in json.dumps(payload)


def test_status_unauthenticated_contract(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:] == ["login", "status"]:
                print("not signed in", file=sys.stderr)
                raise SystemExit(1)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    payload = CodexCliProvider().status().to_dict()

    assert payload["status"] == "unauthenticated"
    assert payload["credential_present"] is False
    assert payload["authenticated"] is False
    assert payload["next_command"] == "agentos llm login --provider codex"
    assert "agentos llm login --provider codex" in payload["recovery"]
    assert "not signed in" not in json.dumps(payload)


def test_stream_jsonl_success_events(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"text": "OK"}))
                print(json.dumps({"content": " done"}))
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]

    assert [event["type"] for event in events] == ["start", "message_delta", "message_delta", "done"]
    assert events[1]["text"] == "OK"
    assert events[2]["text"] == " done"
    assert events[-1]["usage"]["input_chars"] == 5


def test_stream_parses_codex_item_completed_agent_message(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print("Reading additional input from stdin...")
                print(json.dumps({"type": "thread.started"}))
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "OK"}}))
                print("2026-07-18T00:00:00Z  WARN codex_file_watcher: shutdown warning")
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]

    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert events[1]["text"] == "OK"


def test_stream_parses_reasoning_and_tool_call_items(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"type": "item.completed", "item": {"type": "reasoning", "text": "Thinking it through"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "function_call", "name": "list_files", "arguments": {"path": "."}}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "function_call_output", "output": "a.txt"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Done"}}))
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]

    assert [event["type"] for event in events] == [
        "start",
        "reasoning",
        "tool_call",
        "tool_result",
        "message_delta",
        "done",
    ]
    assert events[1]["text"] == "Thinking it through"
    assert events[2]["metadata"]["name"] == "list_files"
    assert events[2]["metadata"]["arguments"] == {"path": "."}
    assert events[3]["metadata"]["summary"] == "a.txt"
    assert events[4]["text"] == "Done"


def test_stream_emits_before_process_exit(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            import time
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"text": "first"}), flush=True)
                time.sleep(0.35)
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    started_at = time.monotonic()
    stamps: list[tuple[str, float]] = []
    for event in CodexCliProvider(timeout_seconds=2).stream_once("hello"):
        stamps.append((event.type, time.monotonic() - started_at))

    first_message_at = next(timestamp for event_type, timestamp in stamps if event_type == "message_delta")
    done_at = next(timestamp for event_type, timestamp in stamps if event_type == "done")

    assert first_message_at < done_at
    assert done_at - first_message_at >= 0.2


def test_stream_redacts_secrets_from_reasoning_and_tool_call_items(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"type": "item.completed", "item": {"type": "reasoning", "text": "token=SENTINEL_SECRET"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "local_shell_call", "command": ["cat", "SENTINEL_SECRET"]}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "local_shell_call_output", "output": "leak SENTINEL_SECRET"}}))
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]
    serialized = json.dumps(events)

    assert "SENTINEL_SECRET" not in serialized


def test_failure_event_is_sanitized(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print("token=SENTINEL_SECRET", file=sys.stderr)
                raise SystemExit(7)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]
    serialized = json.dumps(events)

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["provider"] == "codex"
    assert events[0]["mode"] == "account-login"
    assert events[0]["error"]["code"] == "codex_cli_failed"
    assert events[0]["metadata"]["retryable"] is True
    assert "SENTINEL_SECRET" not in serialized


def test_cli_status_codex_json(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:] == ["login", "status"]:
                print("signed in")
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    result = runner.invoke(app, ["llm", "status", "--json", "--provider", "codex"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "codex"
    assert payload["mode"] == "account-login"
    assert payload["status"] == "authenticated"
    assert payload["authenticated"] is True


def test_cli_login_logout_codex_json(tmp_path, monkeypatch):
    calls = tmp_path / "calls.txt"
    fake = write_fake_codex(
        tmp_path,
        dedent(
            f"""
            with open({str(calls)!r}, "a", encoding="utf-8") as handle:
                handle.write(" ".join(sys.argv[1:]) + "\\n")
            if sys.argv[1:] == ["login"]:
                raise SystemExit(0)
            if sys.argv[1:] == ["logout"]:
                raise SystemExit(0)
            if sys.argv[1:] == ["login", "status"]:
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    login = runner.invoke(app, ["llm", "login", "--provider", "codex", "--json"])
    logout = runner.invoke(app, ["llm", "logout", "--provider", "codex", "--json"])

    assert login.exit_code == 0
    assert logout.exit_code == 0
    assert json.loads(login.stdout)["action"] == "login"
    assert json.loads(login.stdout)["status"] == "authenticated"
    assert json.loads(logout.stdout)["action"] == "logout"
    assert json.loads(logout.stdout)["status"] == "logged_out"
    assert "login" in calls.read_text(encoding="utf-8")
    assert "logout" in calls.read_text(encoding="utf-8")


def test_cli_run_codex_jsonl(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print(json.dumps({"text": "OK"}))
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    result = runner.invoke(app, ["run", "--json", "--once", "hello", "--provider", "codex"])

    assert result.exit_code == 0
    events = json_lines(result.stdout)
    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert all(event["provider"] == "codex" for event in events)
    assert all(event["mode"] == "account-login" for event in events)
    assert events[1]["text"] == "OK"


def test_cli_run_codex_failure_exits_nonzero_and_redacts(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        dedent(
            """
            if sys.argv[1:3] == ["exec", "--json"]:
                print("api_key=SENTINEL_SECRET", file=sys.stderr)
                raise SystemExit(7)
            raise SystemExit(2)
            """
        ),
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    result = runner.invoke(app, ["run", "--json", "--once", "hello", "--provider", "codex"])

    assert result.exit_code == 1
    events = json_lines(result.stdout)
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["error"]["code"] == "codex_cli_failed"
    assert events[0]["metadata"]["retryable"] is True
    assert "SENTINEL_SECRET" not in result.stdout
    assert "SENTINEL_SECRET" not in result.stderr


def test_redaction_missing_cli_does_not_expose_configured_path(monkeypatch):
    monkeypatch.setenv("CODEX_CLI_PATH", "/tmp/SENTINEL_SECRET/codex")
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    result = runner.invoke(app, ["llm", "status", "--json", "--provider", "codex"])

    assert result.exit_code == 0
    assert "SENTINEL_SECRET" not in result.stdout
    assert "SENTINEL_SECRET" not in result.stderr
    assert json.loads(result.stdout)["status"] == "missing_cli"


def test_opt_in_real_codex_status_smoke_is_guarded(monkeypatch):
    if os.environ.get("AGENTOS_CODEX_INTEGRATION") != "1":
        assert os.environ.get("AGENTOS_CODEX_INTEGRATION") != "1"
        return

    monkeypatch.delenv("CODEX_CLI_PATH", raising=False)
    result = runner.invoke(app, ["llm", "status", "--json", "--provider", "codex"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["provider"] == "codex"
    assert payload["mode"] == "account-login"
