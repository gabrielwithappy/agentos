from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from agentos.conversation.context import build_context
from agentos.conversation.types import (
    BranchHead,
    ConversationMessage,
    ConversationState,
    ProviderContinuation,
    new_message_id,
)
from agentos.llm.session import stream_context as session_stream_context
from agentos.llm.tools.registry import ToolName, execute_tool, get_tool_schemas
from agentos.llm.types import InvocationMessage, InvocationRequest, LLMEvent
from agentos.terminal.events import new_turn_id

TERMINAL_EVENT_TYPES = {"done", "error"}

DEFAULT_ACCOUNT = "default"
"""AgentOS does not yet support multiple simultaneous accounts per
provider; every continuation is scoped under this single account slot
until multi-account support exists."""

# Hard cap on tool_call -> execute -> re-invoke iterations within a single
# user turn, so a provider that keeps requesting tools can never hang the
# turn indefinitely.
MAX_TOOL_CALLS_PER_TURN = 10

TOOL_READ_CONFIRM_ENV_VAR = "AGENTOS_TOOL_READ_CONFIRM"

def _read_confirm_required() -> bool:
    return os.environ.get(TOOL_READ_CONFIRM_ENV_VAR, "").strip() not in ("", "0", "false", "False")


class ConversationRuntime:
    """Owns one session's `ConversationState` and performs every turn as a
    single atomic state transition.

    `submit_turn()` never mutates `self.state` incrementally: it builds a
    candidate next state locally, streams normalized provider events to the
    caller, and only assigns the new state to `self.state` once, after the
    stream's terminal `done` event. If the caller stops consuming the
    generator early (cancel) or the stream ends in an `error` event or an
    exception, `self.state` is left exactly as it was before the call — no
    user message, no assistant message, no continuation, and no branch head
    move are ever partially committed.

    `transport_session_epoch` is a fresh identifier per `ConversationRuntime`
    instance (i.e. per process/resume), so a `ProviderContinuation` persisted
    by a previous process instance never matches this instance's epoch and
    is never reused across restart/resume — callers fall back to full
    message replay instead, per the continuation validity contract in
    `agentos.conversation.types.ProviderContinuation`.
    """

    def __init__(
        self,
        state: ConversationState,
        *,
        provider: str,
        model: str,
        account: str = DEFAULT_ACCOUNT,
    ):
        self._state = state
        self._provider_name = provider
        self._model = model
        self._account = account
        self._transport_session_epoch = str(uuid4())
        self.last_context_build_ms: float | None = None

    @property
    def state(self) -> ConversationState:
        return self._state

    def fork_branch(self, *, from_message_id: str | None = None, label: str | None = None) -> str:
        """Creates a new branch that shares the immutable message prefix up
        to `from_message_id` (default: the active branch's current head) —
        no messages are copied, only a new `BranchHead` pointer.

        The new branch always starts with `continuation=None`, never
        inheriting the source branch's `ProviderContinuation`: once forked,
        the two branches can diverge, and reusing a continuation issued for
        the parent's (potentially different, future) history on the fork's
        first turn would silently smuggle context the fork never actually
        had. Returns the new branch's id.
        """
        parent_branch = self._state.active_branch()
        fork_point = from_message_id if from_message_id is not None else parent_branch.head_message_id
        new_branch_id = str(uuid4())
        new_branch = BranchHead(
            branch_id=new_branch_id,
            label=label or f"fork-of-{parent_branch.label}",
            head_message_id=fork_point,
            parent_branch_id=parent_branch.branch_id,
            fork_point_message_id=fork_point,
            continuation=None,
        )
        branches = dict(self._state.branches)
        branches[new_branch_id] = new_branch
        self._state = replace(self._state, branches=branches)
        return new_branch_id

    def switch_branch(self, branch_id: str) -> None:
        if branch_id not in self._state.branches:
            raise KeyError(branch_id)
        self._state = replace(self._state, active_branch_id=branch_id)

    def submit_turn(
        self,
        text: str,
        *,
        max_messages: int | None = None,
        force_full_replay: bool = False,
        cwd: Path | None = None,
        allowed_read_paths: tuple[Path, ...] = (),
        blocked_read_roots: tuple[Path, ...] = (),
        tool_names: list[ToolName] | None = None,
        confirm_tool_call: Callable[[str, dict], bool] | None = None,
    ) -> Iterator[LLMEvent]:
        """`force_full_replay=True` is a benchmarking/diagnostic hook: it
        skips continuation reuse for this turn even if a valid one exists,
        so callers can directly compare continuation-reuse vs
        full-normalized-context-replay timing for the same branch state.
        It never affects what gets committed afterward — the turn still
        commits (and may still record) a fresh continuation normally.

        `tool_names` (default: none — the pre-tool-loop behavior) declares
        which tools are offered to the provider this turn. When the provider
        responds with a `tool_call` instead of `done`, this method executes
        the tool, appends a `role="tool"` message, and re-invokes the
        provider with the extended context — up to `MAX_TOOL_CALLS_PER_TURN`
        times — before yielding the final assistant response. Turns with no
        tool_call are unaffected: exactly one provider call, identical to
        the pre-tool-loop behavior.

        `confirm_tool_call(name, arguments) -> bool`, if given and
        `AGENTOS_TOOL_READ_CONFIRM` is truthy, is called before each tool
        execution; a `False` return aborts the loop without executing the
        tool (a `tool_call_denied` event is yielded and the turn ends with
        whatever assistant text has been produced so far, same as hitting
        the call-count limit).
        """
        branch_id = self._state.active_branch_id
        candidate_state = self._append_message(
            self._state,
            branch_id,
            ConversationMessage(
                id=new_message_id(),
                role="user",
                text=text,
                source="user",
            ),
        )

        turn_id = new_turn_id()
        assistant_text_parts: list[str] = []
        latest_continuation_handle: str | None = None
        resolved_cwd = cwd if cwd is not None else Path.cwd()
        tool_schemas = get_tool_schemas(tool_names) if tool_names else None
        force_replay_this_call = force_full_replay
        tool_calls_executed = 0

        while True:
            continuation = (
                None
                if force_replay_this_call
                else self._resolve_continuation(candidate_state.branches[branch_id])
            )
            context_build_started = time.perf_counter()
            built = build_context(candidate_state, branch_id, max_messages=max_messages)
            self.last_context_build_ms = (time.perf_counter() - context_build_started) * 1000
            request = InvocationRequest(
                messages=[InvocationMessage(role=m.role, text=m.text) for m in built.messages],
                continuation=continuation.handle if continuation is not None else None,
                tools=tool_schemas,
            )

            terminal_event: LLMEvent | None = None
            pending_tool_call: LLMEvent | None = None

            for event in session_stream_context(request, provider=self._provider_name):
                if event.type == "message_delta" and event.text:
                    assistant_text_parts.append(event.text)
                handle = event.metadata.get("continuation") if event.metadata else None
                if handle:
                    latest_continuation_handle = handle
                if event.type == "tool_call":
                    pending_tool_call = event
                if event.type in TERMINAL_EVENT_TYPES:
                    terminal_event = event
                yield event

            if terminal_event is not None and terminal_event.type == "error":
                # Cancelled or unsupported-capability: commit nothing.
                return

            if terminal_event is not None and terminal_event.type == "done":
                break

            if pending_tool_call is None:
                # Cancelled (caller stopped consuming before a terminal
                # event): commit nothing.
                return

            if tool_calls_executed >= MAX_TOOL_CALLS_PER_TURN:
                assistant_text_parts.append(
                    "\n\n[도구 호출 한도 초과: 한 턴에 최대 "
                    f"{MAX_TOOL_CALLS_PER_TURN}회까지만 도구를 호출할 수 있습니다.]"
                )
                yield LLMEvent(
                    type="tool_call_limit_reached",
                    provider=self._provider_name,
                    mode="tool",
                    metadata={"limit": MAX_TOOL_CALLS_PER_TURN},
                )
                break

            tool_name = pending_tool_call.metadata.get("name", "")
            tool_arguments = pending_tool_call.metadata.get("arguments", {})

            if _read_confirm_required() and confirm_tool_call is not None:
                if not confirm_tool_call(tool_name, tool_arguments):
                    yield LLMEvent(
                        type="tool_call_denied",
                        provider=self._provider_name,
                        mode="tool",
                        metadata={"name": tool_name},
                    )
                    break

            result = execute_tool(tool_name, tool_arguments, cwd=resolved_cwd, allowed_read_paths=allowed_read_paths, blocked_read_roots=blocked_read_roots)
            tool_calls_executed += 1
            candidate_state = self._append_message(
                candidate_state,
                branch_id,
                ConversationMessage(
                    id=new_message_id(),
                    role="tool",
                    text=result.content,
                    source=self._provider_name,
                    tool_name=tool_name,
                    turn_id=turn_id,
                ),
            )
            yield LLMEvent(
                type="tool_result",
                provider=self._provider_name,
                mode="tool",
                metadata={"name": tool_name, "is_error": result.is_error, "blocked": result.blocked},
            )
            # A fresh tool message just changed the branch prefix, so any
            # previously resolved continuation no longer matches what the
            # provider last saw — force a full context replay next call.
            force_replay_this_call = True

        final_state = self._commit_assistant_message(
            candidate_state,
            branch_id=branch_id,
            turn_id=turn_id,
            text="".join(assistant_text_parts),
            continuation_handle=latest_continuation_handle,
        )
        self._state = final_state

    def _resolve_continuation(self, branch: BranchHead) -> ProviderContinuation | None:
        continuation = branch.continuation
        if continuation is None:
            return None
        if continuation.matches(
            provider=self._provider_name,
            model=self._model,
            account=self._account,
            branch_id=branch.branch_id,
            transport_session_epoch=self._transport_session_epoch,
        ):
            return continuation
        return None

    def _commit_assistant_message(
        self,
        state: ConversationState,
        *,
        branch_id: str,
        turn_id: str,
        text: str,
        continuation_handle: str | None,
    ) -> ConversationState:
        state = self._append_message(
            state,
            branch_id,
            ConversationMessage(
                id=new_message_id(),
                role="assistant",
                text=text,
                source=self._provider_name,
                turn_id=turn_id,
            ),
        )
        if continuation_handle is None:
            return state

        branch = state.branches[branch_id]
        continuation = ProviderContinuation(
            provider=self._provider_name,
            model=self._model,
            account=self._account,
            branch_id=branch_id,
            transport_session_epoch=self._transport_session_epoch,
            handle=continuation_handle,
        )
        branches = dict(state.branches)
        branches[branch_id] = replace(branch, continuation=continuation)
        return replace(state, branches=branches)

    @staticmethod
    def _append_message(
        state: ConversationState, branch_id: str, message: ConversationMessage
    ) -> ConversationState:
        branch = state.branches[branch_id]
        messages = dict(state.messages)
        messages[message.id] = message
        parent_message_id = dict(state.parent_message_id)
        parent_message_id[message.id] = branch.head_message_id
        branches = dict(state.branches)
        branches[branch_id] = replace(branch, head_message_id=message.id)
        return replace(state, messages=messages, parent_message_id=parent_message_id, branches=branches)
