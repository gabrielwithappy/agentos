import json
import os
from unittest import mock

from typer.testing import CliRunner

from agentos.cli import app
from agentos.llm.registry import (
    DuplicateProviderError,
    ProviderRegistry,
    UnsupportedCapabilityError,
    provider_capabilities,
    stream_context as registry_stream_context,
    supported_providers,
)
from agentos.llm.providers.mock import MOCK_MESSAGE, MockProvider
from agentos.llm.redaction import redact_text
from agentos.llm.session import stream_context, unsupported_capability_event
from agentos.llm.types import InvocationMessage, InvocationRequest, ProviderCapabilities

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

    assert [event["type"] for event in events] == [
        "start",
        "reasoning",
        "tool_call",
        "tool_result",
        "message_delta",
        "done",
    ]
    assert all(event["provider"] == "mock" for event in events)
    assert all(event["mode"] == "mock" for event in events)
    assert MOCK_MESSAGE in events[4]["text"]
    assert events[5]["usage"]["input_chars"] == 5


def test_registry_reports_supported_provider_names():
    assert supported_providers() == ("codex", "codex-cli", "mock")


def test_registry_rejects_duplicate_provider_registration():
    registry = ProviderRegistry()
    registry.register("mock", MockProvider)

    with mock.patch.dict(os.environ, {}, clear=False):
        try:
            registry.register("mock", MockProvider)
        except DuplicateProviderError as exc:
            assert exc.provider == "mock"
        else:
            raise AssertionError("Duplicate provider registration should fail.")


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


def test_login_command_streams_hints_to_stderr_and_keeps_json_stdout_clean(tmp_path, monkeypatch):
    """Regression: `agentos llm login` previously called `build_login_payload()`
    directly, discarding any `login_updates()` hints entirely — a one-shot
    CLI invocation showed nothing about where to sign in until the whole
    (possibly failing) flow finished. Hints must now reach the user via
    stderr, while `--json` stdout stays exactly the final sanitized payload."""
    from agentos.commands import llm as llm_command

    monkeypatch.setattr(
        llm_command,
        "iter_login_updates",
        lambda provider: iter(
            [
                {"type": "hint", "text": "Open this URL to sign in:\nhttps://auth.openai.com/oauth/authorize?x=1"},
                {
                    "type": "result",
                    "payload": {
                        "provider": provider,
                        "mode": "account-login",
                        "status": "authenticated",
                        "authenticated": True,
                        "credential_present": True,
                        "persistent_credential": True,
                        "message": "Codex sign-in completed.",
                    },
                },
            ]
        ),
    )

    result = runner.invoke(app, ["llm", "login", "--provider", "codex", "--json"])

    assert result.exit_code == 0
    assert "https://auth.openai.com/oauth/authorize" in result.stderr
    payload = json.loads(result.stdout)
    assert payload["action"] == "login"
    assert payload["authenticated"] is True


def test_run_json_once_stream_events(tmp_path):
    from unittest import mock as _mock
    with _mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path / "home")}, clear=False):
        result = runner.invoke(app, ["run", "--json", "--once", "hello", "--provider", "mock"])

    assert result.exit_code == 0
    events = json_lines(result.stdout)
    assert [event["type"] for event in events] == [
        "start",
        "reasoning",
        "tool_call",
        "tool_result",
        "message_delta",
        "done",
    ]
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
    assert "codex, codex-cli, mock" in event["error"]["message"]
    assert "codex, codex-cli, mock" in event["recovery"]
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


def test_invocation_request_holds_ordered_messages_and_continuation_handle():
    messages = [
        InvocationMessage(role="system", text="be terse"),
        InvocationMessage(role="user", text="hi"),
        InvocationMessage(role="assistant", text="hello"),
    ]
    request = InvocationRequest(messages=messages, continuation="opaque-handle-1")

    assert request.messages == messages
    assert request.continuation == "opaque-handle-1"
    assert request.metadata == {}


def test_stream_once_is_a_stateless_compatibility_shim():
    events = list(MockProvider().stream_once("hello"))

    assert events[0].type == "start"
    assert events[-1].type == "done"
    assert not any("continuation" in event.metadata for event in events)


def test_provider_capability_defaults_to_context_aware_false_for_legacy_provider():
    class LegacyProvider:
        name = "legacy"
        mode = "legacy"

        def status(self):
            raise NotImplementedError

        def login(self):
            raise NotImplementedError

        def logout(self):
            raise NotImplementedError

        def stream_once(self, prompt):
            raise NotImplementedError

    capabilities = provider_capabilities(LegacyProvider())

    assert capabilities == ProviderCapabilities(context_aware=False)


def test_mock_provider_stream_context_consumes_multi_turn_messages():
    request = InvocationRequest(
        messages=[
            InvocationMessage(role="user", text="turn one"),
            InvocationMessage(role="assistant", text="reply one"),
            InvocationMessage(role="user", text="turn two"),
        ]
    )

    events = list(registry_stream_context(MockProvider(), request))
    final_text = next(e.text for e in events if e.type == "message_delta")

    assert "turn one" in final_text
    assert "turn two" in final_text


def test_stream_context_raises_unsupported_capability_error_for_non_context_aware_provider():
    class LegacyProvider:
        name = "legacy"
        mode = "legacy"

        def status(self):
            raise NotImplementedError

        def login(self):
            raise NotImplementedError

        def logout(self):
            raise NotImplementedError

        def stream_once(self, prompt):
            raise NotImplementedError

    try:
        list(registry_stream_context(LegacyProvider(), InvocationRequest(messages=[])))
    except UnsupportedCapabilityError as exc:
        assert exc.provider == "legacy"
    else:
        raise AssertionError("Expected UnsupportedCapabilityError.")


def test_stream_context_unsupported_capability_error_is_sanitized_and_offers_recovery():
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        request = InvocationRequest(
            messages=[InvocationMessage(role="user", text="token=SENTINEL_SECRET")]
        )
        events = list(stream_context(request, provider="codex-cli"))

        assert len(events) == 1
        event = events[0]
        assert event.type == "error"
        assert event.error["code"] == "unsupported_capability"
        assert "codex-cli" in event.recovery
        assert "--once" in event.recovery
        assert "SENTINEL_SECRET" not in str(event.to_dict())


def test_unsupported_capability_event_redacts_provider_name():
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        event = unsupported_capability_event("provider-SENTINEL_SECRET")

        assert "SENTINEL_SECRET" not in str(event.to_dict())
