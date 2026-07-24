from __future__ import annotations

import json
import os
from unittest import mock

from agentos.conversation.persistence import (
    CONVERSATION_SESSION_SCHEMA_VERSION,
    commit_turn,
    compact_branch,
    empty_state,
    migrate_legacy_state,
    next_sequence,
    rebuild_state,
    write_snapshot,
)
from agentos.conversation.runtime import ConversationRuntime
from agentos.conversation.types import ConversationMessage, TRUSTED_SYSTEM_SOURCE


def _paths(tmp_path, name: str = "s1"):
    return tmp_path / f"{name}.conversation-events.jsonl", tmp_path / f"{name}.conversation-snapshot.json"


# --- Step 1: snapshot / rebuild / schema_version / v1_migration / committed_turn / fsync / rename / sequence / crash / old_session ---


def test_snapshot_schema_version_is_stable(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    state = empty_state("s1")
    commit_turn(events_path, snapshot_path, sequence=0, state=state)

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == CONVERSATION_SESSION_SCHEMA_VERSION


def test_committed_turn_event_is_appended_and_fsynced(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    state = empty_state("s1")
    commit_turn(events_path, snapshot_path, sequence=0, state=state)

    lines = events_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["type"] == "turn_committed"
    assert record["sequence"] == 0


def test_sequence_increments_and_next_sequence_reads_it_back(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    state = empty_state("s1")
    assert next_sequence(events_path) == 0

    commit_turn(events_path, snapshot_path, sequence=0, state=state)
    assert next_sequence(events_path) == 1

    commit_turn(events_path, snapshot_path, sequence=1, state=state)
    assert next_sequence(events_path) == 2


def test_rebuild_state_returns_none_for_a_brand_new_session(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    assert rebuild_state(events_path, snapshot_path) is None


def test_rebuild_state_round_trips_a_committed_turn(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter(
            [_ev("start"), _ev("message_delta", text="hi"), _ev("done")]
        ),
    ):
        list(runtime.submit_turn("hello"))

    commit_turn(events_path, snapshot_path, sequence=0, state=runtime.state)
    rebuilt = rebuild_state(events_path, snapshot_path)

    assert rebuilt is not None
    assert [m.role for m in rebuilt.branch_messages("main")] == ["user", "assistant"]
    assert rebuilt.branch_messages("main")[0].text == "hello"


def test_rebuild_state_discards_an_orphaned_rename_interrupted_tmp_snapshot(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    state = empty_state("s1")
    commit_turn(events_path, snapshot_path, sequence=0, state=state)

    # Simulate a crash between the fsync'd `.tmp` write and the rename: a
    # `.tmp` file exists but was never promoted to `snapshot_path`.
    tmp_path_file = snapshot_path.with_name(snapshot_path.name + ".tmp")
    tmp_path_file.write_text('{"garbage": true}', encoding="utf-8")

    rebuilt = rebuild_state(events_path, snapshot_path)

    assert rebuilt is not None
    assert rebuilt.session_id == "s1"  # rebuilt from the real (renamed) snapshot, `.tmp` ignored


def test_rebuild_state_replays_events_committed_after_the_last_snapshot(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    first_state = empty_state("s1")
    commit_turn(events_path, snapshot_path, sequence=0, state=first_state)

    # Simulate "commit-before-snapshot" crash: a second turn's event is
    # durably appended, but the snapshot write for it never happened
    # (snapshot on disk still reflects sequence=0).
    from agentos.conversation.persistence import append_turn_committed_event
    from agentos.conversation.runtime import ConversationRuntime as _Runtime

    runtime = _Runtime(first_state, provider="mock", model="mock-model")
    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter([_ev("start"), _ev("message_delta", text="hi"), _ev("done")]),
    ):
        list(runtime.submit_turn("second turn"))
    append_turn_committed_event(events_path, sequence=1, state=runtime.state)
    # No write_snapshot() call here — snapshot on disk is stale at sequence=0.

    rebuilt = rebuild_state(events_path, snapshot_path)

    assert rebuilt is not None
    assert len(rebuilt.branch_messages("main")) == 2  # user + assistant from the un-snapshotted turn


def test_v1_migration_reads_legacy_session_log_without_writing_to_it(tmp_path):
    legacy_events = [
        {"type": "input_received", "turn_id": "t1", "payload": {"length": 5}},
        {"type": "provider_event", "turn_id": "t1", "payload": {"type": "message_delta", "text": "hi there"}},
        {"type": "provider_event", "turn_id": "t1", "payload": {"type": "done"}},
    ]

    state = migrate_legacy_state("legacy-session", legacy_events)

    messages = state.branch_messages(state.active_branch_id)
    assert [m.role for m in messages] == ["user", "assistant"]
    assert "not persisted" in messages[0].text
    assert messages[1].text == "hi there"
    # Read-only: migration takes a list of already-loaded events, it never
    # opens or writes the legacy session's own files.


def test_old_session_migration_never_attaches_a_provider_continuation():
    legacy_events = [
        {"type": "input_received", "turn_id": "t1", "payload": {"length": 5}},
        {"type": "provider_event", "turn_id": "t1", "payload": {"type": "message_delta", "text": "hi"}},
    ]

    state = migrate_legacy_state("legacy-session", legacy_events)

    assert state.active_branch().continuation is None


def test_rebuild_never_attaches_a_reusable_continuation_after_a_crash_or_resume(tmp_path):
    events_path, snapshot_path = _paths(tmp_path)
    state = empty_state("s1")
    commit_turn(events_path, snapshot_path, sequence=0, state=state)

    rebuilt = rebuild_state(events_path, snapshot_path)
    assert rebuilt.active_branch().continuation is None


def test_resume_conversation_state_falls_back_to_v1_migration_for_an_old_session(tmp_path, monkeypatch):
    from agentos.terminal.events import CliEvent, wrap_provider_event
    from agentos.terminal.sessions import append_event, create_session, resume_conversation_state

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    session_id = create_session(provider="mock", mode="interactive")
    append_event(
        session_id,
        CliEvent("input_received", session_id, "t1", "mock", "interactive", {"length": 5}).to_dict(),
    )
    append_event(
        session_id,
        wrap_provider_event(
            {"type": "message_delta", "text": "hi there"},
            session_id=session_id,
            turn_id="t1",
            provider="mock",
            mode="interactive",
        ),
    )

    state = resume_conversation_state(session_id)

    messages = state.branch_messages(state.active_branch_id)
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[1].text == "hi there"
    assert state.active_branch().continuation is None


def test_resume_conversation_state_prefers_new_format_over_legacy_when_both_exist(tmp_path, monkeypatch):
    from agentos.terminal.events import CliEvent
    from agentos.terminal.sessions import (
        append_event,
        conversation_events_path,
        conversation_snapshot_path,
        create_session,
        resume_conversation_state,
    )

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    session_id = create_session(provider="mock", mode="interactive")
    append_event(
        session_id,
        CliEvent("input_received", session_id, "t1", "mock", "interactive", {"length": 5}).to_dict(),
    )

    new_format_state = empty_state(session_id)
    commit_turn(
        conversation_events_path(session_id),
        conversation_snapshot_path(session_id),
        sequence=0,
        state=new_format_state,
    )

    resumed = resume_conversation_state(session_id)
    assert resumed.session_id == session_id
    assert resumed.messages == {}  # the new-format (empty) state, not a v1-migrated one


def test_resume_conversation_state_returns_a_brand_new_empty_state_for_an_unknown_session(tmp_path, monkeypatch):
    from agentos.terminal.sessions import resume_conversation_state

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    state = resume_conversation_state(str(__import__("uuid").uuid4()))
    assert state.messages == {}


def _ev(event_type: str, **kwargs):
    from agentos.llm.types import LLMEvent

    kwargs.setdefault("provider", "mock")
    kwargs.setdefault("mode", "mock")
    return LLMEvent(type=event_type, **kwargs)


# --- Step 2: fork / branch / resume / active_branch / context ---


def test_fork_branch_shares_immutable_prefix_without_copying_messages():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter([_ev("start"), _ev("message_delta", text="hi"), _ev("done")]),
    ):
        list(runtime.submit_turn("hello"))

    original_message_count = len(runtime.state.messages)
    new_branch_id = runtime.fork_branch(label="alt")

    assert len(runtime.state.messages) == original_message_count  # no messages copied
    assert runtime.state.branches[new_branch_id].parent_branch_id == "main"
    assert (
        runtime.state.branch_messages(new_branch_id)
        == runtime.state.branch_messages("main")
    )


def test_fork_branch_isolates_continuation_from_the_source_branch(monkeypatch):
    runtime = ConversationRuntime(empty_state("s1"), provider="codex", model="gpt-5-codex")

    def fake_stream_context(request, provider="codex"):
        yield _ev("start", provider="codex", mode="account-login")
        yield _ev("done", provider="codex", mode="account-login", metadata={"continuation": "resp_1"})

    import agentos.conversation.runtime as runtime_module

    monkeypatch.setattr(runtime_module, "session_stream_context", fake_stream_context)
    list(runtime.submit_turn("hi"))
    assert runtime.state.active_branch().continuation is not None

    new_branch_id = runtime.fork_branch(label="alt")

    assert runtime.state.branches[new_branch_id].continuation is None
    assert runtime.state.active_branch().continuation is not None  # source branch untouched


def test_switch_branch_changes_active_branch_and_resume_selects_correct_context():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter([_ev("start"), _ev("message_delta", text="reply-a"), _ev("done")]),
    ):
        list(runtime.submit_turn("turn-a"))

    fork_id = runtime.fork_branch(label="alt")
    runtime.switch_branch(fork_id)

    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter([_ev("start"), _ev("message_delta", text="reply-b"), _ev("done")]),
    ):
        list(runtime.submit_turn("turn-b"))

    assert runtime.state.active_branch_id == fork_id
    fork_texts = [m.text for m in runtime.state.branch_messages(fork_id)]
    main_texts = [m.text for m in runtime.state.branch_messages("main")]
    assert fork_texts == ["turn-a", "reply-a", "turn-b", "reply-b"]
    assert main_texts == ["turn-a", "reply-a"]  # main branch is unaffected by the fork's new turn


def test_switch_branch_raises_for_an_unknown_branch_id():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    try:
        runtime.switch_branch("does-not-exist")
    except KeyError:
        pass
    else:
        raise AssertionError("Expected KeyError for an unknown branch id.")


# --- Step 3: compact / persistence / redact / secret ---


def test_compact_branch_keeps_newest_messages_and_summarizes_the_rest():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    for index in range(3):
        with mock.patch(
            "agentos.conversation.runtime.session_stream_context",
            lambda request, provider="mock", i=index: iter(
                [_ev("start"), _ev("message_delta", text=f"reply-{i}"), _ev("done")]
            ),
        ):
            list(runtime.submit_turn(f"turn-{index}"))

    compacted = compact_branch(runtime.state, "main", keep_last=2)
    messages = compacted.branch_messages("main")

    assert messages[0].source == "compaction"
    assert "compacted" in messages[0].text
    assert [m.text for m in messages[1:]] == ["turn-2", "reply-2"]


def test_compact_branch_is_a_deterministic_no_op_when_nothing_needs_dropping():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    with mock.patch(
        "agentos.conversation.runtime.session_stream_context",
        lambda request, provider="mock": iter([_ev("start"), _ev("message_delta", text="hi"), _ev("done")]),
    ):
        list(runtime.submit_turn("hello"))

    compacted = compact_branch(runtime.state, "main", keep_last=10)
    assert compacted is runtime.state


def test_compact_branch_never_mutates_messages_still_used_by_another_branch():
    runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
    for index in range(3):
        with mock.patch(
            "agentos.conversation.runtime.session_stream_context",
            lambda request, provider="mock", i=index: iter(
                [_ev("start"), _ev("message_delta", text=f"reply-{i}"), _ev("done")]
            ),
        ):
            list(runtime.submit_turn(f"turn-{index}"))

    fork_id = runtime.fork_branch(label="alt")
    compacted_state = compact_branch(runtime.state, "main", keep_last=1)

    # The fork's chain is read straight from `parent_message_id`/`messages`,
    # neither of which `compact_branch` mutated for pre-existing ids.
    assert [m.text for m in compacted_state.branch_messages(fork_id)] == [
        "turn-0",
        "reply-0",
        "turn-1",
        "reply-1",
        "turn-2",
        "reply-2",
    ]


def test_compact_branch_requires_contiguous_trusted_system_prefix():
    state = empty_state("s1")
    branch_id = state.active_branch_id
    from agentos.conversation.persistence import _append_message

    # A non-trusted message inserted before a "trusted" system message
    # breaks the contiguous-root-prefix precondition `compact_branch`
    # documents and requires.
    state = _append_message(
        state, branch_id, ConversationMessage(id="m1", role="user", text="hi", source="user")
    )
    state = _append_message(
        state,
        branch_id,
        ConversationMessage(id="m2", role="system", text="sys", source=TRUSTED_SYSTEM_SOURCE),
    )

    try:
        compact_branch(state, branch_id, keep_last=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for a non-contiguous trusted system prefix.")


def test_snapshot_and_events_never_expose_raw_sentinel_secret(tmp_path):
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        events_path, snapshot_path = _paths(tmp_path)
        runtime = ConversationRuntime(empty_state("s1"), provider="codex", model="gpt-5-codex")

        def fake_stream_context(request, provider="codex"):
            yield _ev("start", provider="codex", mode="account-login")
            yield _ev(
                "done",
                provider="codex",
                mode="account-login",
                metadata={"continuation": "resp_SENTINEL_SECRET_looking_handle"},
            )

        import agentos.conversation.runtime as runtime_module

        with mock.patch.object(runtime_module, "session_stream_context", fake_stream_context):
            list(runtime.submit_turn("token=SENTINEL_SECRET"))

        commit_turn(events_path, snapshot_path, sequence=0, state=runtime.state)

        assert "SENTINEL_SECRET" not in snapshot_path.read_text(encoding="utf-8")
        assert "SENTINEL_SECRET" not in events_path.read_text(encoding="utf-8")


def test_compacted_persistence_snapshot_never_exposes_raw_secret(tmp_path):
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"}):
        events_path, snapshot_path = _paths(tmp_path)
        runtime = ConversationRuntime(empty_state("s1"), provider="mock", model="mock-model")
        with mock.patch(
            "agentos.conversation.runtime.session_stream_context",
            lambda request, provider="mock": iter(
                [_ev("start"), _ev("message_delta", text="token=SENTINEL_SECRET"), _ev("done")]
            ),
        ):
            list(runtime.submit_turn("token=SENTINEL_SECRET"))

        compacted = compact_branch(runtime.state, "main", keep_last=0)
        write_snapshot(snapshot_path, state=compacted, last_event_sequence=0)

        assert "SENTINEL_SECRET" not in snapshot_path.read_text(encoding="utf-8")
