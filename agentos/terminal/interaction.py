from __future__ import annotations

import sys
from itertools import count
from pathlib import Path

from rich.console import Console

from agentos.commands import hook as hook_command
from agentos.conversation.bootstrap import find_bootstrap_message
from agentos.llm.tools.approval import approval_prompt
from agentos.terminal.tui.renderers import render_event
from agentos.llm.tools.registry import ALL_TOOL_NAMES
from agentos.terminal.skills import global_skill_read_paths, global_skills_dir
from agentos.conversation.persistence import commit_turn, next_sequence
from agentos.conversation.runtime import ConversationRuntime
from agentos.llm.session import UnsupportedProviderError, unsupported_provider_event
from agentos.terminal.events import CliEvent, new_turn_id, wrap_provider_event
from agentos.terminal.hooks import HookError, apply_input_hooks
from agentos.terminal.paths import initialize_state
from agentos.terminal.sessions import (
    append_event,
    conversation_events_path,
    conversation_snapshot_path,
    create_session,
    list_sessions,
    read_session,
    resume_conversation_state,
    SessionError,
)

console = Console()

SHELL_LOGIN_RECOVERY_TEXT = (
    "AgentOS-owned Codex sign-in is required.\n"
    "Open another terminal and run: agentos llm login --provider codex\n"
    "Then return here and run /status."
)


def _default_model_for_provider(provider: str) -> str:
    if provider in ("codex", "codex-cli"):
        from agentos.llm.providers.codex_native import DEFAULT_MODEL

        return DEFAULT_MODEL
    if provider == "claude":
        from agentos.llm.providers.claude_native import DEFAULT_MODEL as CLAUDE_DEFAULT_MODEL

        return CLAUDE_DEFAULT_MODEL
    return f"{provider}-default"


_tool_call_counter = count(1)


def _confirm_tool_call(name: str, arguments: dict) -> bool:
    """Blocks on a synchronous prompt since this CLI path is single-threaded.

    Uses the same `approval_prompt()` renderer as the TUI modal. The old
    version printed only `arguments["path"]`, which meant a `bash` call
    showed an empty string where the command should be — the user approved
    a shell command they could not see. Defaults to deny on empty input.
    """
    body = approval_prompt(
        name, arguments, cwd=Path.cwd(), call_number=next(_tool_call_counter)
    )
    console.print(body)
    answer = console.input("실행할까요? [y/N] ")
    return answer.strip().lower() in ("y", "yes")


TOOLS_ANNOUNCEMENT = (
    "AgentOS가 파일을 찾고·읽고·고치고(write/edit) 명령을 실행할(bash) 수 있습니다. "
    "되돌리기 어려운 도구는 실행 전마다 승인을 요청합니다."
)


def _print_bootstrap_banner(runtime: ConversationRuntime) -> None:
    console.print(TOOLS_ANNOUNCEMENT)
    message = find_bootstrap_message(runtime.state)
    if message is None:
        return
    file_count = len(message.metadata.get("bootstrap_context_paths", []))
    skill_count = len(message.metadata.get("bootstrap_skill_names", []))
    console.print(f"부트스트랩 컨텍스트: {file_count}개 파일, {skill_count}개 스킬 로드됨 — /status로 확인")


def run_interactive(provider: str = "mock", yolo: bool = False) -> int:
    initialize_state()
    session_id = create_session(provider=provider, mode="interactive")
    runtime = ConversationRuntime(
        resume_conversation_state(session_id), provider=provider, model=_default_model_for_provider(provider)
    )
    console.print(f"AgentOS interactive session {session_id}. Type /help or /exit.")
    _print_bootstrap_banner(runtime)
    if yolo:
        console.print("YOLO: enabled (write/edit/bash approvals skipped; Ctrl+C cancels)")
    cancelling = False
    while True:
        try:
            raw = input(f"agentos[{provider}]> ")
        except EOFError:
            console.print("Session closed.")
            return 0
        except KeyboardInterrupt:
            if cancelling:
                print("\nExiting after cancellation.", file=sys.stderr)
                return 130
            cancelling = True
            print("\nTurn cancelled. You can enter another prompt or /exit.", file=sys.stderr)
            continue
        cancelling = False
        if raw.strip() in {"/exit", "exit", "quit"}:
            console.print("Session closed.")
            return 0
        if raw.strip() == "/help":
            console.print("/help /status /session /hooks /clear /exit")
            continue
        if raw.strip() == "/status":
            console.print(f"provider={provider} session={session_id}")
            bootstrap_message = find_bootstrap_message(runtime.state)
            if bootstrap_message is None:
                console.print("bootstrap_context: none")
            else:
                paths = bootstrap_message.metadata.get("bootstrap_context_paths", [])
                skill_names = bootstrap_message.metadata.get("bootstrap_skill_names", [])
                blocked_files = bootstrap_message.metadata.get("bootstrap_blocked_files", [])
                truncated_files = bootstrap_message.metadata.get("bootstrap_truncated_files", [])
                console.print(f"bootstrap_context_files ({len(paths)}):")
                for path in paths:
                    console.print(f"  {path}")
                console.print(f"bootstrap_skills ({len(skill_names)}):")
                for name in skill_names:
                    console.print(f"  {name}")
                console.print(f"bootstrap_blocked_files ({len(blocked_files)}):")
                for blocked in blocked_files:
                    reasons = ", ".join(blocked.get("reasons", []))
                    console.print(f"  {blocked.get('path')} ({reasons})")
                console.print(f"bootstrap_truncated_files ({len(truncated_files)}):")
                for path in truncated_files:
                    console.print(f"  {path}")
            continue
        if raw.strip() == "/session":
            console.print(f"session_id={session_id}")
            console.print("Usage: /session list | show <id> | resume <id>")
            continue
        if raw.strip() == "/session list":
            rows = list_sessions()
            if not rows:
                console.print("No sessions found.")
            for row in rows:
                console.print(f"{row['session_id']} {row['provider']} {row['mode']} {row['updated_at']}")
            continue
        if raw.strip().startswith("/session show "):
            target = raw.strip().split(maxsplit=2)[2]
            try:
                meta, events = read_session(target)
                console.print(f"session_id={meta['session_id']} events={len(events)} provider={meta['provider']}")
            except SessionError as exc:
                print(str(exc), file=sys.stderr)
            continue
        if raw.strip().startswith("/session resume "):
            target = raw.strip().split(maxsplit=2)[2]
            try:
                meta, _ = read_session(target)
                session_id = meta["session_id"]
                provider = meta["provider"]
                runtime = ConversationRuntime(
                    resume_conversation_state(session_id),
                    provider=provider,
                    model=_default_model_for_provider(provider),
                )
                console.print(f"Resumed session {session_id}.")
                _print_bootstrap_banner(runtime)
            except SessionError as exc:
                print(str(exc), file=sys.stderr)
            continue
        if raw.strip() == "/hooks":
            hook_command.list_()
            continue
        if raw.strip() == "/clear":
            console.clear()
            continue
        if raw.startswith("/"):
            print("Unknown command. Next: /help", file=sys.stderr)
            continue
        turn_id = new_turn_id()
        try:
            prompt = apply_input_hooks(raw)
        except HookError as exc:
            print(f"Hook {exc.hook} failed: {exc}", file=sys.stderr)
            continue
        append_event(
            session_id,
            CliEvent("input_received", session_id, turn_id, provider, "interactive", {"length": len(prompt)}).to_dict(),
        )
        has_error = False
        try:
            for event in runtime.submit_turn(
                prompt,
                cwd=Path.cwd(),
                tool_names=list(ALL_TOOL_NAMES),
                allowed_read_paths=global_skill_read_paths(),
                blocked_read_roots=(global_skills_dir(),),
                confirm_tool_call=_confirm_tool_call,
                yolo=yolo,
            ):
                payload = event.to_dict()
                append_event(
                    session_id,
                    wrap_provider_event(
                        payload,
                        session_id=session_id,
                        turn_id=turn_id,
                        provider=provider,
                        mode="interactive",
                        branch_id=runtime.state.active_branch_id,
                    ),
                )
                if payload["type"] == "tool_call":
                    metadata = payload.get("metadata") or {}
                    path = (metadata.get("arguments") or {}).get("path", "")
                    console.print(f"읽는 중: {path}")
                if payload["type"] == "tool_call_limit_reached":
                    console.print(render_event(payload))
                if payload["type"] == "legacy_tool_result_unavailable":
                    console.print(render_event(payload))
                if payload["type"] == "message_delta" and payload.get("text"):
                    console.print(payload["text"])
                if payload["type"] == "error":
                    has_error = True
                    error_payload = payload.get("error") or {}
                    if error_payload.get("code") == "unauthenticated":
                        print(SHELL_LOGIN_RECOVERY_TEXT, file=sys.stderr)
                    else:
                        print(error_payload.get("message", "Provider error."), file=sys.stderr)
            if not has_error:
                events_path = conversation_events_path(session_id)
                snapshot_path = conversation_snapshot_path(session_id)
                commit_turn(events_path, snapshot_path, sequence=next_sequence(events_path), state=runtime.state)
        except UnsupportedProviderError:
            payload = unsupported_provider_event(provider).to_dict()
            append_event(session_id, payload)
            print(payload["error"]["message"], file=sys.stderr)
            return 1
