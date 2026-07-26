from __future__ import annotations

import os
from dataclasses import replace
from unittest import mock

from agentos.conversation import runtime as runtime_module
from agentos.conversation.runtime import MAX_TOOL_CALLS_PER_TURN, ConversationRuntime
from agentos.conversation.types import (
    BranchHead,
    ConversationMessage,
    ConversationState,
    ProviderContinuation,
)
from agentos.llm.types import InvocationMessage, LLMEvent
from agentos.terminal.events import wrap_provider_event


def _empty_state(session_id: str = "s1", branch_id: str = "main") -> ConversationState:
    return ConversationState(
        session_id=session_id,
        active_branch_id=branch_id,
        branches={branch_id: BranchHead(branch_id=branch_id, label="main", head_message_id=None)},
        messages={},
        parent_message_id={},
    )


# --- Step 1: submit_turn / user_commit / assistant_commit / event_stream ---


def test_submit_turn_user_commit_precedes_the_provider_stream_call(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    captured_message_counts = []

    def fake_stream_context(request, provider="mock"):
        # The AgentOS response-style system prompt is prepended at request
        # assembly time and is not part of the conversation, so count only
        # the messages that came from `ConversationState`.
        captured_message_counts.append(
            len([m for m in request.messages if m.role != "system"])
        )
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("hello"))

    assert captured_message_counts == [1]
    assert [e.type for e in events] == ["start", "message_delta", "done"]


def test_submit_turn_assistant_commit_happens_only_after_a_done_event(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hello ")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="world")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hi"))

    messages = runtime.state.branch_messages("main")
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[0].text == "hi"
    assert messages[1].text == "hello world"


def test_submit_turn_event_stream_is_forwarded_to_the_caller_unmodified(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    canned = [
        LLMEvent(type="start", provider="mock", mode="mock"),
        LLMEvent(type="reasoning", provider="mock", mode="mock", text="thinking"),
        LLMEvent(type="tool_call", provider="mock", mode="mock", metadata={"name": "x"}),
        LLMEvent(type="tool_result", provider="mock", mode="mock", metadata={"name": "x"}),
        LLMEvent(type="message_delta", provider="mock", mode="mock", text="done text"),
        LLMEvent(type="done", provider="mock", mode="mock"),
    ]

    def fake_stream_context(request, provider="mock"):
        yield from canned

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("hi"))
    assert events == canned


# --- Step 2: cancel / error / atomic / continuation ---


def test_submit_turn_cancel_before_terminal_event_leaves_state_unchanged(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="partial")
        # Never reaches `done` — this branch is unreachable once the caller
        # closes the generator below, simulating a mid-stream cancel.
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    generator = runtime.submit_turn("hi")
    next(generator)
    next(generator)
    generator.close()

    assert runtime.state is state
    assert runtime.state.messages == {}


def test_submit_turn_error_event_does_not_commit_user_or_assistant_message(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="error", provider="mock", mode="mock", error={"code": "boom", "message": "failed"})

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("hi"))

    assert events[-1].type == "error"
    assert runtime.state is state
    assert runtime.state.messages == {}


def test_submit_turn_commits_state_as_a_single_atomic_transition(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    seen_states_during_stream = []

    def fake_stream_context(request, provider="mock"):
        seen_states_during_stream.append(runtime.state)
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        seen_states_during_stream.append(runtime.state)
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hi"))

    assert all(s is state for s in seen_states_during_stream)
    assert runtime.state is not state


def test_submit_turn_stores_continuation_scoped_to_provider_model_branch_and_epoch(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="codex", model="gpt-5-codex")

    def fake_stream_context(request, provider="codex"):
        yield LLMEvent(type="start", provider="codex", mode="account-login")
        yield LLMEvent(
            type="done",
            provider="codex",
            mode="account-login",
            metadata={"continuation": "resp_1"},
        )

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hi"))

    continuation = runtime.state.active_branch().continuation
    assert continuation is not None
    assert continuation.handle == "resp_1"
    assert continuation.matches(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id="main",
        transport_session_epoch=runtime._transport_session_epoch,
    )


def test_submit_turn_never_reuses_a_continuation_from_a_different_transport_session_epoch(monkeypatch):
    branch_id = "main"
    stale_continuation = ProviderContinuation(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id=branch_id,
        transport_session_epoch="stale-epoch-from-a-previous-process",
        handle="resp_stale",
    )
    state = ConversationState(
        session_id="s1",
        active_branch_id=branch_id,
        branches={
            branch_id: BranchHead(
                branch_id=branch_id, label="main", head_message_id=None, continuation=stale_continuation
            )
        },
        messages={},
        parent_message_id={},
    )
    runtime = ConversationRuntime(state, provider="codex", model="gpt-5-codex")
    captured = {}

    def fake_stream_context(request, provider="codex"):
        captured["continuation"] = request.continuation
        yield LLMEvent(type="start", provider="codex", mode="account-login")
        yield LLMEvent(type="done", provider="codex", mode="account-login")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hi"))

    assert captured["continuation"] is None


# --- Step 3: jsonl / redact / event_envelope ---


def test_submit_turn_event_envelope_preserves_llm_event_identity():
    state = _empty_state()

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield canned_delta
        yield LLMEvent(type="done", provider="mock", mode="mock")

    canned_delta = LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi", usage={"input_chars": 1})

    with mock.patch.object(runtime_module, "session_stream_context", fake_stream_context):
        runtime = ConversationRuntime(state, provider="mock", model="mock-model")
        events = list(runtime.submit_turn("hi"))

    assert events[1] is canned_delta
    assert isinstance(events[1], LLMEvent)


def test_submit_turn_events_stay_compatible_with_existing_jsonl_wrap_provider_event(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("hi"))
    wrapped = [
        wrap_provider_event(
            event.to_dict(),
            session_id="s1",
            turn_id="t1",
            provider="mock",
            mode="mock",
            branch_id=runtime.state.active_branch_id,
        )
        for event in events
    ]

    assert [w["type"] for w in wrapped] == ["start", "message_delta", "done"]
    assert all(w["branch_id"] == "main" for w in wrapped)
    assert all(w["schema_version"] for w in wrapped)


def test_submit_turn_redacts_secret_from_normalized_events_jsonl_and_continuation(monkeypatch):
    # `InvocationRequest` construction here intentionally still carries the
    # raw user text — redaction at that boundary is owned by
    # `build_transport_request()` (Task 3, tested in test_codex_transport.py)
    # right before it crosses the network boundary. This test covers what
    # `ConversationRuntime` itself owns: normalized events already redacted
    # upstream by the real provider adapter must still carry no secret
    # through JSONL wrapping, and the persisted continuation handle must
    # never surface raw via `to_dict()`.
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        state = _empty_state()
        runtime = ConversationRuntime(state, provider="codex", model="gpt-5-codex")

        def fake_stream_context(request, provider="codex"):
            yield LLMEvent(type="start", provider="codex", mode="account-login")
            yield LLMEvent(
                type="message_delta",
                provider="codex",
                mode="account-login",
                text="ok, redacted upstream: [REDACTED]",
                metadata={"continuation": "resp_1"},
            )
            yield LLMEvent(
                type="done", provider="codex", mode="account-login", metadata={"continuation": "resp_1"}
            )

        monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

        events = list(runtime.submit_turn("hi"))
        wrapped = [
            wrap_provider_event(
                event.to_dict(),
                session_id="s1",
                turn_id="t1",
                provider="codex",
                mode="account-login",
                branch_id=runtime.state.active_branch_id,
            )
            for event in events
        ]

        assert all("SENTINEL_SECRET" not in str(event.to_dict()) for event in events)
        assert all("SENTINEL_SECRET" not in str(line) for line in wrapped)
        continuation = runtime.state.active_branch().continuation
        assert continuation is not None
        assert "SENTINEL_SECRET" not in str(continuation.to_dict())
        assert continuation.to_dict().get("handle") is None


def test_submit_turn_force_full_replay_ignores_a_valid_continuation(monkeypatch):
    branch_id = "main"
    valid_continuation = ProviderContinuation(
        provider="codex",
        model="gpt-5-codex",
        account="default",
        branch_id=branch_id,
        transport_session_epoch="epoch-1",
        handle="resp_1",
    )
    state = ConversationState(
        session_id="s1",
        active_branch_id=branch_id,
        branches={
            branch_id: BranchHead(
                branch_id=branch_id, label="main", head_message_id=None, continuation=valid_continuation
            )
        },
        messages={},
        parent_message_id={},
    )
    runtime = ConversationRuntime(state, provider="codex", model="gpt-5-codex")
    runtime._transport_session_epoch = "epoch-1"  # force a matching epoch for this test
    captured = {}

    def fake_stream_context(request, provider="codex"):
        captured["continuation"] = request.continuation
        yield LLMEvent(type="start", provider="codex", mode="account-login")
        yield LLMEvent(type="done", provider="codex", mode="account-login")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hi", force_full_replay=True))

    assert captured["continuation"] is None


# --- Milestone 4/5/6: tool_call -> execute -> re-invoke agentic loop ---


def test_submit_turn_tool_call_loop_executes_read_and_reinvokes(tmp_path, monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    (tmp_path / "AGENTS.md").write_text("hello from agents md", encoding="utf-8")

    call_count = {"n": 0}

    def fake_stream_context(request, provider="mock"):
        call_count["n"] += 1
        if call_count["n"] == 1:
            assert request.tools is not None
            yield LLMEvent(type="start", provider="mock", mode="mock")
            yield LLMEvent(
                type="tool_call",
                provider="mock",
                mode="mock",
                metadata={"name": "read", "arguments": {"path": "AGENTS.md"}},
            )
            return
        assert any(m.role == "tool" for m in request.messages)
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="final answer")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("read AGENTS.md", cwd=tmp_path, tool_names=["read"]))

    assert "tool_call" in [e.type for e in events]
    assert "tool_result" in [e.type for e in events]
    assert call_count["n"] == 2

    branch = runtime.state.active_branch()
    messages = runtime.state.branch_messages(branch.branch_id)
    assert [m.role for m in messages] == ["user", "tool", "assistant"]
    assert "hello from agents md" in messages[1].text
    assert messages[1].tool_name == "read"
    assert messages[2].text == "final answer"


def test_submit_turn_without_tool_names_runs_a_single_provider_call(monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    call_count = {"n": 0}

    def fake_stream_context(request, provider="mock"):
        call_count["n"] += 1
        assert request.tools is None
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    list(runtime.submit_turn("hello"))

    assert call_count["n"] == 1


def test_submit_turn_tool_call_limit_stops_loop_and_annotates_assistant_text(tmp_path, monkeypatch):
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    (tmp_path / "AGENTS.md").write_text("content", encoding="utf-8")

    call_count = {"n": 0}

    def fake_stream_context(request, provider="mock"):
        call_count["n"] += 1
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(
            type="tool_call",
            provider="mock",
            mode="mock",
            metadata={"name": "read", "arguments": {"path": "AGENTS.md"}},
        )

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    events = list(runtime.submit_turn("loop forever", cwd=tmp_path, tool_names=["read"]))

    assert call_count["n"] == MAX_TOOL_CALLS_PER_TURN + 1
    assert "tool_call_limit_reached" in [e.type for e in events]

    branch = runtime.state.active_branch()
    messages = runtime.state.branch_messages(branch.branch_id)
    assistant_message = messages[-1]
    assert assistant_message.role == "assistant"
    assert "도구 호출 한도 초과" in assistant_message.text
    tool_messages = [m for m in messages if m.role == "tool"]
    assert len(tool_messages) == MAX_TOOL_CALLS_PER_TURN


def test_submit_turn_read_confirm_env_var_off_executes_without_confirmation(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENTOS_TOOL_READ_CONFIRM", raising=False)
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    (tmp_path / "AGENTS.md").write_text("content", encoding="utf-8")
    confirm_calls = []

    def fake_stream_context(request, provider="mock"):
        if not any(m.role == "tool" for m in request.messages):
            yield LLMEvent(type="start", provider="mock", mode="mock")
            yield LLMEvent(
                type="tool_call",
                provider="mock",
                mode="mock",
                metadata={"name": "read", "arguments": {"path": "AGENTS.md"}},
            )
            return
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="done")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    def confirm(name, arguments):
        confirm_calls.append((name, arguments))
        return True

    list(runtime.submit_turn("read it", cwd=tmp_path, tool_names=["read"], confirm_tool_call=confirm))

    assert confirm_calls == []


def test_submit_turn_read_confirm_env_var_on_waits_for_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_TOOL_READ_CONFIRM", "1")
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    (tmp_path / "AGENTS.md").write_text("content", encoding="utf-8")
    confirm_calls = []

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(
            type="tool_call",
            provider="mock",
            mode="mock",
            metadata={"name": "read", "arguments": {"path": "AGENTS.md"}},
        )

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    def deny(name, arguments):
        confirm_calls.append((name, arguments))
        return False

    events = list(runtime.submit_turn("read it", cwd=tmp_path, tool_names=["read"], confirm_tool_call=deny))

    assert confirm_calls == [("read", {"path": "AGENTS.md"})]
    assert "tool_call_denied" in [e.type for e in events]
    branch = runtime.state.active_branch()
    messages = runtime.state.branch_messages(branch.branch_id)
    assert all(m.role != "tool" for m in messages)


def _write_tool_stream(monkeypatch, runtime):
    """Provider that asks for a `write` once, then finishes."""

    def fake_stream_context(request, provider="mock"):
        if not any(m.role == "tool" for m in request.messages):
            yield LLMEvent(type="start", provider="mock", mode="mock")
            yield LLMEvent(
                type="tool_call",
                provider="mock",
                mode="mock",
                metadata={"name": "write", "arguments": {"path": "out.txt", "content": "x"}},
            )
            return
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="done")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)


def test_mutating_tool_is_denied_without_confirm_callback(tmp_path, monkeypatch):
    """No approval path must mean no execution — never unrestricted execution."""
    monkeypatch.delenv("AGENTOS_TOOL_READ_CONFIRM", raising=False)
    runtime = ConversationRuntime(_empty_state(), provider="mock", model="mock-model")
    _write_tool_stream(monkeypatch, runtime)

    events = list(runtime.submit_turn("write it", cwd=tmp_path, tool_names=["write"]))

    assert "tool_call_denied" in [e.type for e in events]
    assert not (tmp_path / "out.txt").exists()


def test_mutating_tool_always_confirms_regardless_of_env(tmp_path, monkeypatch):
    """`AGENTOS_TOOL_READ_CONFIRM` is off by default; a write must still ask."""
    monkeypatch.delenv("AGENTOS_TOOL_READ_CONFIRM", raising=False)
    runtime = ConversationRuntime(_empty_state(), provider="mock", model="mock-model")
    _write_tool_stream(monkeypatch, runtime)
    confirm_calls = []

    def confirm(name, arguments):
        confirm_calls.append((name, arguments))
        return True

    list(
        runtime.submit_turn(
            "write it", cwd=tmp_path, tool_names=["write"], confirm_tool_call=confirm
        )
    )

    assert confirm_calls == [("write", {"path": "out.txt", "content": "x"})]
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "x"


def test_readonly_tool_confirmation_still_env_gated(tmp_path, monkeypatch):
    """The mutating policy must not leak into read-only tools."""
    monkeypatch.delenv("AGENTOS_TOOL_READ_CONFIRM", raising=False)
    runtime = ConversationRuntime(_empty_state(), provider="mock", model="mock-model")
    (tmp_path / "AGENTS.md").write_text("content", encoding="utf-8")

    def fake_stream_context(request, provider="mock"):
        if not any(m.role == "tool" for m in request.messages):
            yield LLMEvent(type="start", provider="mock", mode="mock")
            yield LLMEvent(
                type="tool_call",
                provider="mock",
                mode="mock",
                metadata={"name": "list", "arguments": {}},
            )
            return
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)

    # No callback at all: a read-only tool still runs.
    events = list(runtime.submit_turn("list it", cwd=tmp_path, tool_names=["list"]))
    assert "tool_call_denied" not in [e.type for e in events]


def test_response_style_prompt_precedes_project_context(monkeypatch):
    """AgentOS previously sent no system prompt at all, so the project
    context (when present) was the only guidance the model received. The
    style prompt must come first so a project document cannot redefine it."""
    from agentos.llm.prompt import AGENTOS_RESPONSE_STYLE_PROMPT

    state = _empty_state()
    project_message = ConversationMessage(
        id="bootstrap",
        role="system",
        text="<project_context>...</project_context>",
        source="trusted-system",
    )
    branch = state.branches[state.active_branch_id]
    state = replace(
        state,
        messages={**state.messages, project_message.id: project_message},
        branches={
            **state.branches,
            branch.branch_id: replace(branch, head_message_id=project_message.id),
        },
    )
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    captured: list = []

    def fake_stream_context(request, provider="mock"):
        captured.append(request)
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)
    list(runtime.submit_turn("hello"))

    request = captured[0]
    assert request.messages[0].text == AGENTOS_RESPONSE_STYLE_PROMPT
    assert "<project_context>" in request.messages[1].text


def test_prompt_is_not_persisted_to_conversation_state(monkeypatch):
    """Persisting the style prompt would change the session file format and
    the meaning of a replay, so it must never reach `ConversationState`."""
    from agentos.llm.prompt import AGENTOS_RESPONSE_STYLE_PROMPT

    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")

    def fake_stream_context(request, provider="mock"):
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)
    list(runtime.submit_turn("hello"))

    branch = runtime.state.active_branch()
    for message in runtime.state.branch_messages(branch.branch_id):
        assert AGENTOS_RESPONSE_STYLE_PROMPT not in message.text


def test_prompt_reaches_transport_instructions(monkeypatch):
    """`build_transport_request()` turns `role="system"` messages into
    `instructions` — the only channel a Codex Responses call sees them
    through — so the style prompt must actually arrive there."""
    from agentos.llm.prompt import AGENTOS_RESPONSE_STYLE_PROMPT
    from agentos.llm.transports.base import build_transport_request
    from agentos.llm.types import InvocationRequest

    request = InvocationRequest(
        messages=[
            InvocationMessage(role="system", text=AGENTOS_RESPONSE_STYLE_PROMPT),
            InvocationMessage(role="user", text="hi"),
        ],
    )
    built = build_transport_request(model="gpt-5.5", invocation_request=request)
    assert built.instructions == AGENTOS_RESPONSE_STYLE_PROMPT


def test_prompt_is_stable_across_continuation_reuse(monkeypatch):
    """Pins the invariant the plan relies on instead of adding a schema
    field: `instructions` must be identical across a continuation-reuse
    turn within one runtime instance, and a continuation must never be
    reused across a different runtime instance (the invariant rests solely
    on `transport_session_epoch` freshness, not on the handle being
    unreachable)."""
    state = _empty_state()
    runtime = ConversationRuntime(state, provider="mock", model="mock-model")
    captured: list = []

    def fake_stream_context(request, provider="mock"):
        captured.append(request)
        yield LLMEvent(
            type="start", provider="mock", mode="mock", metadata={"continuation": "handle-1"}
        )
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(
            type="done", provider="mock", mode="mock", metadata={"continuation": "handle-1"}
        )

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)
    list(runtime.submit_turn("first"))
    list(runtime.submit_turn("second"))

    assert len(captured) == 2
    assert captured[0].continuation is None
    assert captured[1].continuation == "handle-1"
    assert captured[0].messages[0].text == captured[1].messages[0].text

    other_runtime = ConversationRuntime(runtime.state, provider="mock", model="mock-model")
    other_captured: list = []

    def fake_stream_context_other(request, provider="mock"):
        other_captured.append(request)
        yield LLMEvent(type="start", provider="mock", mode="mock")
        yield LLMEvent(type="message_delta", provider="mock", mode="mock", text="hi")
        yield LLMEvent(type="done", provider="mock", mode="mock")

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context_other)
    list(other_runtime.submit_turn("third"))
    assert other_captured[0].continuation is None
