from __future__ import annotations

import os
from unittest import mock

from agentos.conversation import runtime as runtime_module
from agentos.conversation.runtime import ConversationRuntime
from agentos.conversation.types import BranchHead, ConversationState, ProviderContinuation
from agentos.llm.types import LLMEvent
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
        captured_message_counts.append(len(request.messages))
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
