# 2026-07-24 - AgentOS PI-style session runtime contract

- Expansion Trigger: `2026-07-24-agentos-pi-session-runtime-tui-architecture.md`의 Task 0이 PI mapping, message schema, continuation privacy, snapshot-rebuild, migration policy를 root docs보다 자세히 고정해야 함.
- parent root doc: `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`
- reason for creation: active plan(Task 1-7)의 구현 근거. 재조사 비용이 큰 PI `agent-loop`/Codex Responses continuation 매핑을 압축 요약 없이 보존한다.
- owner: implementation owner
- freshness rule: Refresh when the reviewed session-runtime plan changes, native Codex transport is implemented, or the conversation persistence contract changes.
- status: 현재
- source evidence: `references/pi/packages/agent/src/agent-loop.ts`, `references/pi/packages/ai/src/api/openai-codex-responses.ts`, `agentos/conversation/{types,context}.py`, `agentos/llm/transports/openai_codex_responses.py`, `agentos/llm/auth/openai_codex.py`, `.agents/traces/research/2026-07-24-agentos-pi-session-runtime-tui-architecture.md` inspected on 2026-07-24.
- links back to: `.agentos/project/exec-plans/active/2026-07-24-agentos-pi-session-runtime-tui-architecture.md`; `.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md`; `.agents/traces/research/2026-07-24-agentos-pi-session-runtime-tui-architecture.md`.
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, reviewer authority, or human approval requirements.

## PI mapping

| PI pattern | Source | AgentOS canonical equivalent |
|---|---|---|
| `currentContext.messages` as source of truth | `agent-loop.ts` | `agentos.conversation.ConversationState.messages` + `parent_message_id` chain (implemented in `agentos/conversation/types.py`) |
| `streamAssistantResponse(currentContext, ...)` independent of TUI | `agent-loop.ts` | `ConversationRuntime.submit_turn()` (Task 4; not yet implemented) receives a `BuiltContext`, not a bare prompt |
| `previous_response_id` continuation | `openai-codex-responses.ts` | `agentos.conversation.ProviderContinuation` (opaque, scoped by `(provider, model, account, branch_id, transport_session_epoch)`); native wiring lives in `agentos/llm/transports/openai_codex_responses.py`'s `TransportRequest.previous_response_id` |
| Provider-specific stream chunks parsed below the agent layer | `openai-codex-responses.ts` `mapCodexEvents` | `agentos.llm.transports.openai_codex_responses.map_codex_frame()` normalizes Responses stream frames into `ProviderEvent`, then `CodexNativeProvider._to_llm_event()` normalizes into `LLMEvent` |

## Message schema

`agentos/conversation/types.py` (Task 1, implemented):

- `ConversationMessage`: immutable, `role` (`system|user|assistant|tool`), `text`, `source`, `turn_id`, `tool_name`, `metadata`.
- `is_trusted_system()`: **only** `source == TRUSTED_SYSTEM_SOURCE` (`"agentos-config"`) may act as a provider `system` instruction. Restored JSONL/snapshot data, PI reference text, provider/tool output, and user input that claim `role="system"` are never trusted — they stay in chronological position instead of being pinned as system context. This is the role-escalation defense verified by `tests/test_context_builder.py::test_role_escalation_via_*`.
- `BranchHead`: `branch_id`, `label`, `head_message_id`, `parent_branch_id`, `fork_point_message_id`, `continuation`. Fork creates a new `BranchHead` referencing an existing immutable message prefix; it never copies or mutates prior messages (verified by `test_branch_prefix_only_includes_selected_branch_chain`).
- `ConversationState`: `session_id`, `active_branch_id`, `branches`, `messages` (all messages across all branches, insertion-ordered), `parent_message_id` (parent-chain links used to reconstruct any branch's ordered history via `branch_messages()`).
- Context builder (`agentos/conversation/context.py`, Task 1, implemented): pins trusted system messages first, preserves chronological system/user/assistant/tool order otherwise, always ends on the newest user message, and trims only from the oldest non-pinned end when `max_messages` is set — trimming is reported via `BuiltContext.trimmed`, never silent.

## Continuation privacy

`ProviderContinuation` (`agentos/conversation/types.py`):

- `handle` (the raw provider continuation value) is never included in `to_dict()` — only `handle_present: bool` is exposed.
- `matches(provider, model, account, branch_id, transport_session_epoch)` is the only way to check validity; an opaque handle from one scope (e.g. one branch or one transport-session epoch) is never reused for another.
- Native transport wiring (`agentos/llm/providers/codex_native.py`, Task 3, implemented) already treats `TransportRequest.previous_response_id` and `access_token` as values that must never appear in `LLMEvent`, JSONL, TUI/CLI output, or exception text — verified by `tests/test_codex_transport.py` and `tests/test_cli_contract.py::test_run_once_json_codex_native_authenticated_stream_redacts_secret`.
- The session-runtime plan's continuation scope (`provider, model, account, branch, transport_session_epoch`) reuses this same `ProviderContinuation.matches()` contract; restart/resume must not reuse a persisted `previous_response_id` and must select bounded normalized replay instead (Task 3 of the session-runtime plan, not yet implemented).

## Snapshot-rebuild and migration policy

Not yet implemented (Task 5 of `2026-07-24-agentos-pi-session-runtime-tui-architecture.md`). Contract recorded here so Task 5 has no ambiguity when it starts:

- Write protocol: durable `turn_committed(sequence=N)` event → `snapshot.tmp` write + fsync → atomic rename to `snapshot` → directory fsync. Snapshot stores `last_event_sequence=N`.
- Resume rules:
  - event-before-commit crash → ignore the dangling event.
  - commit-before-snapshot crash → replay from event sequence `N`.
  - temp/rename-interrupted snapshot → discard and rebuild from the event log.
  - rename-after-snapshot crash → accept the snapshot when its `last_event_sequence` matches the latest committed turn.
- Existing `agentos.session/v1` event logs are read-only migration input: they always use replay-only resume and never reuse a persisted provider continuation (their continuation scope predates the native transport's `transport_session_epoch`).

## Migration rules (restated from the durable research note)

1. `stream_once(prompt)` remains only a compatibility shim for mock/stateless callers; it is not the interactive TUI's canonical path once `ConversationRuntime.submit_turn()` exists.
2. The canonical TUI path calls `ConversationRuntime.submit_turn()` once per user action; the runtime — not `AgentOSTui` — determines prior messages and continuation selection.
3. Both the event log and a normalized conversation snapshot are persisted. The event log is audit/replay evidence; the snapshot is the restore accelerator. A mismatch rebuilds from events rather than trusting stale snapshot data.
4. Branching creates a new branch head referencing an existing immutable message prefix; it never overwrites the selected session's history.
5. Context trimming is deterministic, observable as sanitized metadata (`BuiltContext.trimmed`), and preserves system/user/assistant/tool ordering; it never silently discards the newest user instruction or a pending tool result.
6. Native Codex continuation failure falls back first to bounded normalized replay. CLI compatibility (`--provider codex-cli`) is an explicit recovery/debug choice, not an automatic hidden path.
