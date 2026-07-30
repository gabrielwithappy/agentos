from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
import json
from uuid import uuid4

from agentos.conversation.context import build_context
from agentos.conversation.types import (
    BranchHead,
    ConversationMessage,
    ConversationState,
    ProviderContinuation,
    new_message_id,
)
from agentos.llm.prompt import prepend_response_style
from agentos.llm.session import stream_context as session_stream_context
from agentos.llm.tools.registry import ToolName, execute_tool, get_tool_schemas, requires_confirmation
from agentos.llm.tools.types import ToolExecutionResult
from agentos.llm.types import InvocationMessage, InvocationRequest, LLMEvent
from agentos.terminal.events import new_turn_id
from agentos.terminal.logging_setup import get_logger

TERMINAL_EVENT_TYPES = {"done", "error"}

_logger = get_logger("runtime")

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


def _has_pending_codex_correlation(metadata: dict) -> bool:
    return isinstance(metadata.get("call_id"), str) and isinstance(metadata.get("name"), str) and isinstance(metadata.get("arguments"), dict)


def _has_codex_tool_correlation(metadata: dict) -> bool:
    return isinstance(metadata.get("call_id"), str) and isinstance(metadata.get("name"), str) and isinstance(metadata.get("arguments"), str)


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
        yolo: bool = False,
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
        times by default, or without that per-turn cap when `yolo=True` — before yielding the final assistant response. Turns with no
        tool_call are unaffected: exactly one provider call, identical to
        the pre-tool-loop behavior.

        `confirm_tool_call(name, arguments) -> bool` gates tool execution. A
        `False` return aborts the loop without executing the tool (a
        `tool_call_denied` event is yielded and the turn ends with whatever
        assistant text has been produced so far, same as hitting the
        call-count limit). When it is consulted depends on the tool:

        - Tools where `registry.requires_confirmation()` is true (`write`,
          `edit`, `bash`) are always confirmed, regardless of environment.
          Passing no `confirm_tool_call` denies them rather than running
          them unattended.
        - Read-only tools stay opt-in behind `AGENTOS_TOOL_READ_CONFIRM`.
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
            legacy_tool_results = [
                message
                for message in built.messages
                if message.role == "tool" and not _has_codex_tool_correlation(message.metadata)
            ]
            if self._provider_name == "codex" and legacy_tool_results:
                yield LLMEvent(
                    type="legacy_tool_result_unavailable",
                    provider=self._provider_name,
                    mode="tool",
                    recovery="retry the request",
                )
            request = InvocationRequest(
                messages=prepend_response_style(
                    [InvocationMessage(role=m.role, text=m.text, metadata=dict(m.metadata)) for m in built.messages]
                ),
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
                if event.type == "tool_result":
                    # The provider already executed and reported this call
                    # within the same stream (e.g. a demo/mock provider that
                    # narrates tool_call+tool_result together) — nothing is
                    # actually pending for this runtime to execute.
                    pending_tool_call = None
                if event.type in TERMINAL_EVENT_TYPES:
                    terminal_event = event
                yield event

            if terminal_event is not None and terminal_event.type == "error":
                # Cancelled or unsupported-capability: commit nothing.
                return

            # A `tool_call` takes priority over a `done` seen in the same
            # stream: Codex's native transport emits `response.completed`
            # (-> `done`) as the stream terminator for every response,
            # including ones whose only output is a function call — it
            # does not withhold `done` just because a tool_call is
            # pending. Treating `done` as authoritative here would always
            # skip tool execution and commit an empty assistant message.
            if pending_tool_call is None:
                if terminal_event is not None and terminal_event.type == "done":
                    break
                # Cancelled (caller stopped consuming before a terminal
                # event): commit nothing.
                return

            if not yolo and tool_calls_executed >= MAX_TOOL_CALLS_PER_TURN:
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
            if self._provider_name == "codex" and not _has_pending_codex_correlation(pending_tool_call.metadata):
                yield LLMEvent(
                    type="error",
                    provider=self._provider_name,
                    mode="tool",
                    error={"code": "tool_call_uncorrelated", "message": "도구 호출을 연결할 수 없습니다. 같은 요청을 다시 시도하세요."},
                    recovery="retry the request",
                )
                return

            # Mutating tools are checked first and unconditionally: folding
            # them into the env-gated branch below would leave writes and
            # shell commands running unannounced on a default install.
            if requires_confirmation(tool_name) and not yolo:
                approved = (
                    confirm_tool_call(tool_name, tool_arguments)
                    if confirm_tool_call is not None
                    # No approval path means no approval. A caller that
                    # offers no confirmation UI must not thereby get
                    # unrestricted execution.
                    else False
                )
                if not approved:
                    yield LLMEvent(
                        type="tool_call_denied",
                        provider=self._provider_name,
                        mode="tool",
                        metadata={"name": tool_name},
                    )
                    break
            elif _read_confirm_required() and confirm_tool_call is not None:
                if not confirm_tool_call(tool_name, tool_arguments):
                    yield LLMEvent(
                        type="tool_call_denied",
                        provider=self._provider_name,
                        mode="tool",
                        metadata={"name": tool_name},
                    )
                    break

            try:
                result = execute_tool(
                    tool_name,
                    tool_arguments,
                    cwd=resolved_cwd,
                    allowed_read_paths=allowed_read_paths,
                    blocked_read_roots=blocked_read_roots,
                )
            except Exception:
                # A tool executor raising (e.g. a provider sending an
                # integer-typed argument as a string) must never crash the
                # whole turn/worker — surface it as a normal tool-error
                # result so the model and user both see it, and log the
                # traceback so it's diagnosable after the fact.
                _logger.exception(
                    "Tool execution raised: name=%s arguments=%r", tool_name, tool_arguments
                )
                result = ToolExecutionResult(
                    content=f"Error: tool '{tool_name}' failed unexpectedly. See agentos.log for details.",
                    is_error=True,
                )
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
                    metadata={
                        "call_id": pending_tool_call.metadata.get("call_id"),
                        "name": tool_name,
                        "arguments": json.dumps(tool_arguments, ensure_ascii=False, separators=(",", ":")),
                    },
                ),
            )
            yield LLMEvent(
                type="tool_result",
                provider=self._provider_name,
                mode="tool",
                metadata={"name": tool_name, "is_error": result.is_error, "blocked": result.blocked, "summary": result.content},
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
