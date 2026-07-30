from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer

from agentos.llm.redaction import redact_text
from agentos.terminal.hooks_bundle import bundle_script
from agentos.terminal.paths import StateError
from agentos.commands.project import _root


app = typer.Typer(help="Run package-owned vendor hook bridges", add_completion=False)
MAX_STDIN_BYTES = 64 * 1024
TIMEOUT_SECONDS = 10
BRIDGE_MAP = {
    ("codex", "pre-bash"): "check-careful.sh",
    ("codex", "pre-write"): "check-alignment.py",
    ("codex", "post-bash"): "post_tool_use_review.py",
    ("codex", "stop"): "stop_review_gate.py",
    ("claude-code", "pre-bash"): "check-careful.sh",
    ("claude-code", "pre-write"): "check-alignment.py",
    ("claude-code", "post-bash"): "post_tool_use_review.py",
    ("claude-code", "stop"): "stop_review_gate.py",
}


def _payload() -> bytes:
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(raw) > MAX_STDIN_BYTES:
        raise StateError("Hook payload exceeds 64 KiB.")
    try:
        value = json.loads(raw or b"{}")
    except json.JSONDecodeError as exc:
        raise StateError("Hook payload must be a JSON object.") from exc
    if not isinstance(value, dict):
        raise StateError("Hook payload must be a JSON object.")
    return raw or b"{}"


def _child_env(root: Path) -> dict[str, str]:
    allowed: dict[str, str] = {}
    for key, value in os.environ.items():
        if key in {"PATH", "HOME", "LANG"} or key.startswith("LC_"):
            allowed[key] = value
    allowed["AGENTOS_PROJECT_ROOT"] = str(root)
    return allowed


def run_bridge(vendor: str, event: str, payload: bytes, root: Path) -> subprocess.CompletedProcess[bytes]:
    script_name = BRIDGE_MAP.get((vendor, event))
    if script_name is None:
        raise StateError(f"Unsupported vendor hook mapping: {vendor}/{event}")
    script = bundle_script(script_name)
    command = ["/bin/bash", str(script)] if script.suffix == ".sh" else [sys.executable, str(script)]
    try:
        return subprocess.run(
            command,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_child_env(root),
            cwd=root,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise StateError(f"Hook bridge timed out after {TIMEOUT_SECONDS} seconds.") from exc


@app.command("bridge")
def bridge(vendor: str, event: str) -> None:
    """Dispatch one allowlisted native hook event to a bundled script."""
    try:
        root = _root(None)
        completed = run_bridge(vendor, event, _payload(), root)
    except StateError as exc:
        typer.echo(f"Hook bridge failed: {redact_text(str(exc))}", err=True)
        raise typer.Exit(2)
    if completed.stdout:
        typer.echo(redact_text(completed.stdout.decode("utf-8", errors="replace")), nl=False)
    if completed.stderr:
        typer.echo(redact_text(completed.stderr.decode("utf-8", errors="replace")), err=True, nl=False)
    raise typer.Exit(completed.returncode)
