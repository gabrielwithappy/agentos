import json
from pathlib import Path

from agentos.llm.invocation import invoke_once
from agentos.llm.providers.codex_cli import CodexCliProvider
from agentos.runtime.protocol import InvocationEvent, RuntimeRequest, RuntimeTimings


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


def test_request_schema():
    request = RuntimeRequest(
        prompt="hello",
        provider="mock",
        session_id="session-1",
        transport_hint="runtime_warm",
        record_policy="metadata",
    )

    payload = request.to_dict()

    assert payload == {
        "provider": "mock",
        "transport_hint": "runtime_warm",
        "record_policy": "metadata",
        "prompt_chars": 5,
        "session_id": "session-1",
    }


def test_event_schema():
    request = RuntimeRequest(prompt="hello", provider="mock")
    event = InvocationEvent(
        type="message_delta",
        provider="mock",
        mode="mock",
        text="OK",
        request=request,
        timings=RuntimeTimings(bootstrap_ms=1, provider_ms=2, first_event_ms=3, total_ms=4),
    )

    payload = event.to_dict()

    assert payload["type"] == "message_delta"
    assert payload["request"]["provider"] == "mock"
    assert payload["timings"]["first_event_ms"] == 3
    assert json.dumps(payload)


def test_timings_schema():
    payload = RuntimeTimings(
        bootstrap_ms=1.23456,
        provider_ms=2.34567,
        persistence_ms=0.0,
        first_event_ms=3.45678,
        total_ms=4.56789,
    ).to_dict()

    assert payload == {
        "bootstrap_ms": 1.235,
        "provider_ms": 2.346,
        "persistence_ms": 0.0,
        "first_event_ms": 3.457,
        "total_ms": 4.568,
    }


def test_invocation_layer_wraps_provider_events():
    request = RuntimeRequest(prompt="hello", provider="mock", transport_hint="runtime_warm")

    events = [event.to_dict() for event in invoke_once(request)]

    assert [event["type"] for event in events] == [
        "start",
        "reasoning",
        "tool_call",
        "tool_result",
        "message_delta",
        "done",
    ]
    assert all(event["request"]["transport_hint"] == "runtime_warm" for event in events)
    assert all("timings" in event for event in events)
    assert events[0]["metadata"]["runtime"]["schema_version"] == "agentos.invocation-runtime/v1"


def test_codex_facade_bridge(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        """
if sys.argv[1:3] == ["exec", "--json"]:
    print(json.dumps({"text": "OK"}))
    raise SystemExit(0)
raise SystemExit(2)
""",
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    request = RuntimeRequest(prompt="hello", provider="codex-cli", transport_hint="external_cli")
    events = [event.to_dict() for event in invoke_once(request)]

    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
    assert events[1]["provider"] == "codex-cli"
    assert events[1]["request"]["transport_hint"] == "external_cli"


def test_codex_runtime_stream(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        """
if sys.argv[1:3] == ["exec", "--json"]:
    print(json.dumps({"text": "OK"}))
    raise SystemExit(0)
raise SystemExit(2)
""",
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    request = RuntimeRequest(prompt="hello", provider="codex-cli", transport_hint="runtime_warm")
    events = [event.to_dict() for event in invoke_once(request)]

    assert any(event["type"] == "message_delta" for event in events)
    assert all(event["timings"]["first_event_ms"] is not None for event in events)


def test_codex_provider_still_uses_external_cli_compatibility_path(tmp_path, monkeypatch):
    fake = write_fake_codex(
        tmp_path,
        """
if sys.argv[1:3] == ["exec", "--json"]:
    print(json.dumps({"text": "OK"}))
    raise SystemExit(0)
raise SystemExit(2)
""",
    )
    monkeypatch.setenv("CODEX_CLI_PATH", str(fake))

    events = [event.to_dict() for event in CodexCliProvider().stream_once("hello")]

    assert [event["type"] for event in events] == ["start", "message_delta", "done"]
