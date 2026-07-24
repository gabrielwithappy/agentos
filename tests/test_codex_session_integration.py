from __future__ import annotations

import os

from agentos.conversation.runtime import ConversationRuntime
from agentos.conversation.types import BranchHead, ConversationState

MARKER = "AGENTOS_SESSION_MARKER_" + os.urandom(4).hex()


def _empty_state(branch_id: str = "main") -> ConversationState:
    return ConversationState(
        session_id="codex-session-integration",
        active_branch_id=branch_id,
        branches={branch_id: BranchHead(branch_id=branch_id, label="main", head_message_id=None)},
        messages={},
        parent_message_id={},
    )


def test_real_codex_second_turn_recalls_first_turn_marker_via_continuation():
    if os.environ.get("AGENTOS_CODEX_INTEGRATION") != "1":
        # Opt-in only: this test never talks to the real Codex API unless a
        # human has explicitly authenticated and set
        # AGENTOS_CODEX_INTEGRATION=1. The authenticated preflight that
        # gates this file even being invoked lives in the plan's Task 3
        # Step 4 Run command (a `agentos llm status --provider codex --json`
        # check emitting a sanitized `STOP codex-session-integration ...`
        # otherwise); this in-test guard is a second, redundant layer so the
        # file is also safe to run directly with `pytest` outside that gate.
        return

    runtime = ConversationRuntime(_empty_state(), provider="codex", model="gpt-5-codex")

    first_events = list(
        runtime.submit_turn(f"Remember this marker: {MARKER}. Reply with just OK.")
    )
    assert first_events[-1].type == "done", "First turn must succeed under an authenticated opt-in run."

    continuation = runtime.state.active_branch().continuation
    assert continuation is not None, "First turn must produce a continuation handle to prove against."

    second_events = list(
        runtime.submit_turn("What marker did I ask you to remember? Reply with just the marker.")
    )
    assert second_events[-1].type == "done"

    assistant_messages = [m for m in runtime.state.branch_messages("main") if m.role == "assistant"]
    assert MARKER in assistant_messages[-1].text

    all_events = first_events + second_events
    assert all("SENTINEL_SECRET" not in str(event.to_dict()) for event in all_events)
