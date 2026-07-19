from __future__ import annotations

import sys

from rich.console import Console

from agentos.commands import hook as hook_command
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event
from agentos.terminal.events import CliEvent, new_turn_id, wrap_provider_event
from agentos.terminal.hooks import HookError, apply_input_hooks
from agentos.terminal.paths import initialize_state
from agentos.terminal.sessions import append_event, create_session, list_sessions, read_session, SessionError

console = Console()


def run_interactive(provider: str = "mock") -> int:
    initialize_state()
    session_id = create_session(provider=provider, mode="interactive")
    console.print(f"AgentOS interactive session {session_id}. Type /help or /exit.")
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
                console.print(f"Resumed session {session_id}.")
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
        try:
            for event in stream_once(prompt, provider=provider):
                payload = event.to_dict()
                append_event(
                    session_id,
                    wrap_provider_event(
                        payload,
                        session_id=session_id,
                        turn_id=turn_id,
                        provider=provider,
                        mode="interactive",
                    ),
                )
                if payload["type"] == "message_delta" and payload.get("text"):
                    console.print(payload["text"])
                if payload["type"] == "error":
                    print(payload.get("error", {}).get("message", "Provider error."), file=sys.stderr)
        except UnsupportedProviderError:
            payload = unsupported_provider_event(provider).to_dict()
            append_event(session_id, payload)
            print(payload["error"]["message"], file=sys.stderr)
            return 1
