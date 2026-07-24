from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from agentos.conversation.types import (
    CONVERSATION_SCHEMA_VERSION,
    BranchHead,
    ConversationMessage,
    ConversationState,
    new_message_id,
    utc_now,
)
from agentos.llm.redaction import sanitize

CONVERSATION_SESSION_SCHEMA_VERSION = "agentos.conversation-session/v1"

DEFAULT_BRANCH_ID = "main"
DEFAULT_BRANCH_LABEL = "main"

LEGACY_SESSION_SCHEMA_VERSION = "agentos.session/v1"
"""`agentos/terminal/sessions.py`'s pre-runtime session format. Read-only
migration input: legacy sessions are never written to using this module's
protocol, and are always rebuilt via full replay (see `migrate_legacy_state`)."""


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def empty_state(session_id: str, *, branch_id: str = DEFAULT_BRANCH_ID) -> ConversationState:
    return ConversationState(
        session_id=session_id,
        active_branch_id=branch_id,
        branches={branch_id: BranchHead(branch_id=branch_id, label=DEFAULT_BRANCH_LABEL, head_message_id=None)},
        messages={},
        parent_message_id={},
    )


def append_turn_committed_event(events_path: Path, *, sequence: int, state: ConversationState) -> None:
    """Durable step 1 of the commit protocol: append one
    `turn_committed(sequence=N)` line carrying the full post-turn state and
    fsync the file before returning.

    This step happens *before* the snapshot write. A crash between this
    call and `write_snapshot()` (the "commit-before-snapshot" window) is
    always recoverable: `rebuild_state()` replays every `turn_committed`
    event newer than the last good snapshot's `last_event_sequence`, so the
    durable event is picked up on the next resume even if no snapshot ever
    reflected it. A crash *before* this call ("event-before-commit") simply
    means the turn never happened as far as any reader is concerned —
    nothing to recover, by construction there is no event to replay.
    """
    events_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "type": "turn_committed",
            "sequence": sequence,
            "schema_version": CONVERSATION_SESSION_SCHEMA_VERSION,
            "recorded_at": utc_now(),
            "state": sanitize(state.to_dict()),
        },
        sort_keys=True,
    )
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_snapshot(snapshot_path: Path, *, state: ConversationState, last_event_sequence: int) -> None:
    """Durable steps 2-4 of the commit protocol: write `<snapshot>.tmp`,
    fsync it, atomically rename it onto `snapshot_path`, then fsync the
    containing directory so the rename itself is durable.

    A crash before the rename completes (mid-write, or the
    "temp/rename-interrupted" window where `.tmp` exists but the rename
    never landed) leaves only an orphaned `.tmp` file: `rebuild_state()`
    never reads `.tmp` files, so it is silently discarded and superseded by
    the next successful `write_snapshot()` call. A crash *after* the rename
    lands but before the directory fsync ("rename-after-snapshot") is
    accepted as-is on resume: the renamed file's `last_event_sequence`
    already matches the durable event that produced it, so there is nothing
    further to validate — sequence-match is the acceptance criterion.
    """
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = snapshot_path.with_name(snapshot_path.name + ".tmp")
    payload = {
        "schema_version": CONVERSATION_SESSION_SCHEMA_VERSION,
        "last_event_sequence": last_event_sequence,
        "recorded_at": utc_now(),
        "state": sanitize(state.to_dict()),
    }
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, snapshot_path)
    _fsync_dir(snapshot_path.parent)


def commit_turn(events_path: Path, snapshot_path: Path, *, sequence: int, state: ConversationState) -> None:
    """Runs the full durable commit protocol for one turn, in order:
    append-and-fsync the event, then write-fsync-rename-fsync the snapshot.
    """
    append_turn_committed_event(events_path, sequence=sequence, state=state)
    write_snapshot(snapshot_path, state=state, last_event_sequence=sequence)


def rebuild_state(events_path: Path, snapshot_path: Path) -> ConversationState | None:
    """Resume: load the latest valid snapshot (if any), then replay every
    `turn_committed` event whose `sequence` is greater than the snapshot's
    `last_event_sequence`. Each event carries a full state (not a delta),
    so replay is just "take the highest-sequence event past the snapshot" —
    no incremental event application is needed. Returns `None` if there is
    no snapshot and no events log to rebuild from.

    A malformed or unreadable snapshot (partial write that somehow bypassed
    the atomic-rename protocol, e.g. hand-edited or corrupted) is treated
    the same as "no snapshot": rebuild continues from the events log alone.
    """
    best_sequence = -1
    best_state: ConversationState | None = None

    if snapshot_path.is_file():
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            if payload.get("schema_version") == CONVERSATION_SESSION_SCHEMA_VERSION:
                best_state = _state_from_dict(payload["state"])
                best_sequence = int(payload.get("last_event_sequence", -1))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            best_state = None
            best_sequence = -1

    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "turn_committed":
                continue
            sequence = record.get("sequence")
            if not isinstance(sequence, int) or sequence <= best_sequence:
                continue
            try:
                candidate_state = _state_from_dict(record["state"])
            except (KeyError, TypeError, ValueError):
                continue
            best_sequence = sequence
            best_state = candidate_state

    return best_state


def next_sequence(events_path: Path) -> int:
    """The sequence number the next `commit_turn()` call should use: one
    past the highest `sequence` seen in the events log (0 if empty/absent)."""
    if not events_path.is_file():
        return 0
    highest = -1
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        sequence = record.get("sequence")
        if isinstance(sequence, int) and sequence > highest:
            highest = sequence
    return highest + 1


def _message_from_dict(payload: dict[str, Any]) -> ConversationMessage:
    return ConversationMessage(
        id=payload["id"],
        role=payload["role"],
        text=payload["text"],
        source=payload["source"],
        turn_id=payload.get("turn_id"),
        tool_name=payload.get("tool_name"),
        created_at=payload.get("created_at") or utc_now(),
        metadata=dict(payload.get("metadata") or {}),
    )


def _branch_from_dict(payload: dict[str, Any]) -> BranchHead:
    return BranchHead(
        branch_id=payload["branch_id"],
        label=payload["label"],
        head_message_id=payload.get("head_message_id"),
        parent_branch_id=payload.get("parent_branch_id"),
        fork_point_message_id=payload.get("fork_point_message_id"),
        # A snapshot/event's continuation is a sanitized, handle-free
        # `to_dict()` view (see `ProviderContinuation.to_dict()`); the raw
        # handle is never persisted to disk in the first place. This is
        # intentional, not a gap: `ConversationRuntime` mints a fresh
        # `transport_session_epoch` every process start, so a continuation
        # from a previous process could never pass `.matches()` regardless —
        # persisting it would only ever be dead weight, never a reusable
        # handle. Every rebuilt branch head starts with no continuation and
        # the next turn on it falls back to full message replay.
        continuation=None,
        created_at=payload.get("created_at") or utc_now(),
    )


def _state_from_dict(payload: dict[str, Any]) -> ConversationState:
    messages = {mid: _message_from_dict(m) for mid, m in payload["messages"].items()}
    branches = {bid: _branch_from_dict(b) for bid, b in payload["branches"].items()}
    return ConversationState(
        session_id=payload["session_id"],
        active_branch_id=payload["active_branch_id"],
        branches=branches,
        messages=messages,
        parent_message_id=dict(payload["parent_message_id"]),
        schema_version=payload.get("schema_version", CONVERSATION_SCHEMA_VERSION),
    )


def migrate_legacy_state(session_id: str, legacy_events: list[dict[str, Any]]) -> ConversationState:
    """Rebuilds a `ConversationState` from a legacy `agentos.session/v1`
    JSONL event log, read-only.

    The legacy `input_received` event never persisted the user's actual
    prompt text (only `{"length": N}`, by the pre-runtime format's design),
    so a legacy user turn cannot be recovered verbatim. Each legacy turn is
    represented as a synthetic placeholder user message (clearly labeled as
    reconstructed, not original) so branch ordering and turn boundaries are
    preserved, followed by the real assistant/tool text recovered from
    `message_delta`/`tool_call`/`tool_result` payloads. Continuation is
    always absent (`None`): the legacy format predates provider
    continuation entirely, so there is nothing to carry forward — legacy
    sessions always resume via full replay, never continuation reuse.
    """
    state = empty_state(session_id)
    branch_id = state.active_branch_id
    pending_assistant_parts: list[str] = []
    current_turn_id: str | None = None

    def flush_assistant(turn_id: str | None) -> None:
        nonlocal state, pending_assistant_parts
        if not pending_assistant_parts:
            return
        message = ConversationMessage(
            id=new_message_id(),
            role="assistant",
            text="".join(pending_assistant_parts),
            source="legacy-migration",
            turn_id=turn_id,
        )
        state = _append_message(state, branch_id, message)
        pending_assistant_parts = []

    for event in legacy_events:
        event_type = event.get("type")
        turn_id = event.get("turn_id")
        if event_type == "input_received":
            flush_assistant(current_turn_id)
            current_turn_id = turn_id
            length = event.get("payload", {}).get("length")
            placeholder = (
                f"[legacy session: original prompt text was not persisted, length={length} chars]"
                if isinstance(length, int)
                else "[legacy session: original prompt text was not persisted]"
            )
            message = ConversationMessage(
                id=new_message_id(),
                role="user",
                text=placeholder,
                source="legacy-migration",
                turn_id=turn_id,
            )
            state = _append_message(state, branch_id, message)
            continue

        payload = event.get("payload") or {}
        inner_type = payload.get("type")
        if inner_type == "message_delta" and payload.get("text"):
            pending_assistant_parts.append(str(payload["text"]))
        elif inner_type == "tool_result":
            metadata = payload.get("metadata") or {}
            summary = metadata.get("summary")
            if summary:
                pending_assistant_parts.append(f"[tool:{metadata.get('name', '?')}] {summary}")

    flush_assistant(current_turn_id)
    return state


def compact_branch(state: ConversationState, branch_id: str, *, keep_last: int) -> ConversationState:
    """Deterministically shrinks `branch_id`'s chain to its trusted `system`
    prefix plus a synthetic summary message plus the newest `keep_last`
    non-system messages. Never mutates any pre-existing message or
    `parent_message_id` entry — it only adds new entries (a summary message
    plus fresh copies of the kept tail under new ids) and repoints
    `branch_id`'s own `head_message_id`. This makes compaction safe by
    construction with respect to any other branch that still shares part of
    this chain via fork: their `parent_message_id` links are untouched, so
    their view is unaffected regardless of what this branch compacts away.

    Requires the branch's trusted `system` messages (if any) to form a
    contiguous prefix at the root of the chain (each one's own parent is
    `None` or another trusted `system` message) — the only pattern actually
    produced by this codebase (a single system message inserted at session
    start). A non-contiguous trusted-system placement raises `ValueError`
    rather than silently producing a chain that still walks back through
    the "compacted away" region through a system message's real ancestry.
    """
    chain = state.branch_messages(branch_id)
    trusted_system = [m for m in chain if m.is_trusted_system()]
    rest = [m for m in chain if not m.is_trusted_system()]

    cursor: str | None = None
    for message in trusted_system:
        if state.parent_message_id.get(message.id) != cursor:
            raise ValueError(
                "compact_branch requires trusted system messages to form a contiguous root prefix."
            )
        cursor = message.id

    kept_tail = rest[-keep_last:] if keep_last > 0 else []
    dropped = rest[: len(rest) - len(kept_tail)]
    if not dropped:
        return state

    summary_message = ConversationMessage(
        id=new_message_id(),
        role="tool",
        text=f"[compacted: {len(dropped)} earlier messages omitted (ids {dropped[0].id}..{dropped[-1].id})]",
        source="compaction",
        tool_name="conversation-compaction",
        metadata={"compacted_count": len(dropped), "compacted_through_message_id": dropped[-1].id},
    )

    messages = dict(state.messages)
    parent_message_id = dict(state.parent_message_id)
    messages[summary_message.id] = summary_message
    parent_message_id[summary_message.id] = cursor
    cursor = summary_message.id

    for original in kept_tail:
        copy = replace(original, id=new_message_id())
        messages[copy.id] = copy
        parent_message_id[copy.id] = cursor
        cursor = copy.id

    branch = state.branches[branch_id]
    branches = dict(state.branches)
    branches[branch_id] = replace(branch, head_message_id=cursor)
    return replace(state, messages=messages, parent_message_id=parent_message_id, branches=branches)


def _append_message(state: ConversationState, branch_id: str, message: ConversationMessage) -> ConversationState:
    branch = state.branches[branch_id]
    messages = dict(state.messages)
    messages[message.id] = message
    parent_message_id = dict(state.parent_message_id)
    parent_message_id[message.id] = branch.head_message_id
    branches = dict(state.branches)
    branches[branch_id] = replace(branch, head_message_id=message.id)
    return replace(state, messages=messages, parent_message_id=parent_message_id, branches=branches)
