#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import pty
import select
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _run_pty(args: list[str], writes: list[bytes], env: dict[str, str], timeout: float = 5.0) -> tuple[int, str]:
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        args,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        cwd=Path(__file__).resolve().parents[2],
        close_fds=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.time() + timeout
    write_index = 0
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output.extend(chunk)
                prompt_markers = (b"Type a message or / for commands", b"agentos[", b"[y/N]:")
                if write_index < len(writes) and any(marker in output for marker in prompt_markers):
                    os.write(master, writes[write_index])
                    write_index += 1
            if proc.poll() is not None:
                break
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
        return proc.returncode or 0, output.decode("utf-8", errors="replace")
    finally:
        os.close(master)


def _run_with_tty_stdin_redirected_stdout(command: str, env: dict[str, str]) -> int:
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            shlex.split(command),
            stdin=slave,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            close_fds=True,
        )
        os.close(slave)
        slave = -1
        stdout, stderr = proc.communicate(timeout=5)
        if stdout:
            sys.stdout.write(stdout)
        if stderr:
            sys.stderr.write(stderr)
        return proc.returncode or 0
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        if stdout:
            sys.stdout.write(stdout)
        if stderr:
            sys.stderr.write(stderr)
        return 124
    finally:
        if slave != -1:
            os.close(slave)
        os.close(master)


def _assert_interactive(root: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentos-pty-"))
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        env["AGENTOS_HOME"] = str(tmp / "home")
        env["AGENTOS_TUI_TEST_PLAIN"] = "1"
        python = str(root / ".venv" / "bin" / "python") if (root / ".venv" / "bin" / "python").exists() else sys.executable
        code, transcript = _run_pty(
            [python, "-m", "agentos.cli", "run"],
            [b"/help\n", b"/session\n", b"/hooks\n", b"/bogus\n", b"hello\n", b"/exit\n"],
            env,
        )
        assert code == 0, transcript
        assert "Show provider" in transcript
        assert "/session list - List recent sessions" in transcript
        assert "reject_empty" in transcript
        assert "Unknown command. Next: /help" in transcript
        assert "Mock response" in transcript
        session_files = list((tmp / "home" / "sessions").glob("*.jsonl"))
        assert session_files, transcript
        content = session_files[0].read_text(encoding="utf-8")
        assert "agentos.cli-event/v1" in content
        assert '"schema_version"' in content
        assert "SENTINEL_SECRET" not in transcript
        assert "SENTINEL_SECRET" not in content
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _assert_installed_tui(command: str, cwd: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentos-installed-tui-"))
    try:
        env = os.environ.copy()
        env["AGENTOS_HOME"] = str(tmp / "home")
        env["AGENTOS_TUI_TEST_PLAIN"] = "1"
        code, transcript = _run_pty_with_cwd(
            shlex.split(command),
            [b"/help\n", b"/exit\n"],
            env,
            cwd,
        )
        assert code == 0, transcript
        assert "AgentOS" in transcript
        assert "Type a message or / for commands" in transcript
        for label in ("cwd", "provider", "model", "session", "hooks", "mode", "last turn"):
            assert label in transcript
        assert "/status" in transcript
        assert "/session resume" in transcript
        assert "Session closed." in transcript
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _assert_installed_textual_app(python: str) -> None:
    script = r'''
import asyncio
import os
import tempfile
from pathlib import Path

from agentos.terminal.tui.app import AgentOSTui

async def main():
    tmp = Path(tempfile.mkdtemp(prefix="agentos-installed-textual-"))
    os.environ["AGENTOS_HOME"] = str(tmp / "home")
    app = AgentOSTui(provider="mock")
    async with app.run_test() as pilot:
        assert "AgentOS" in str(pilot.app.query_one("#transcript").render())
        assert pilot.app.query_one("#composer").placeholder == "Type a message or / for commands"
        status = str(pilot.app.query_one("#status").render())
        for label in ("cwd", "provider", "model", "session", "hooks", "mode", "last turn"):
            assert label in status
        composer = pilot.app.query_one("#composer")
        composer.value = "/help"
        await pilot.press("enter")
        assert "/session resume" in str(pilot.app.query_one("#transcript").render())
        composer.value = "/exit"
        await pilot.press("enter")

asyncio.run(main())
print("PASS installed-textual-app")
'''
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    proc = subprocess.run([python, "-c", script], text=True, capture_output=True, check=False, env=env)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)


def _run_pty_with_cwd(args: list[str], writes: list[bytes], env: dict[str, str], cwd: Path, timeout: float = 5.0) -> tuple[int, str]:
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        args,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        cwd=cwd,
        close_fds=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.time() + timeout
    write_index = 0
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output.extend(chunk)
                prompt_markers = (b"Type a message or / for commands", b"agentos[", b"[y/N]:")
                if write_index < len(writes) and any(marker in output for marker in prompt_markers):
                    os.write(master, writes[write_index])
                    write_index += 1
            if proc.poll() is not None:
                break
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
        return proc.returncode or 0, output.decode("utf-8", errors="replace")
    finally:
        os.close(master)


def _assert_delete_confirmation(root: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentos-pty-delete-"))
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        env["AGENTOS_HOME"] = str(tmp / "home")
        python = str(root / ".venv" / "bin" / "python") if (root / ".venv" / "bin" / "python").exists() else sys.executable
        subprocess.run([python, "-m", "agentos.cli", "setup"], env=env, cwd=root, check=True, stdout=subprocess.DEVNULL)
        sid = subprocess.check_output(
            [
                python,
                "-c",
                "from agentos.terminal.sessions import create_session; print(create_session())",
            ],
            env=env,
            cwd=root,
            text=True,
        ).strip()
        code, transcript = _run_pty([python, "-m", "agentos.cli", "session", "delete", sid], [b"\n"], env)
        assert code == 0, transcript
        assert "No changes made." in transcript
        assert (tmp / "home" / "sessions" / f"{sid}.jsonl").exists()
        code, transcript = _run_pty([python, "-m", "agentos.cli", "session", "delete", sid], [b"y\n"], env)
        assert code == 0, transcript
        assert "Deleted session" in transcript
        assert not (tmp / "home" / "sessions" / f"{sid}.jsonl").exists()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--stdout-redirect", metavar="COMMAND")
    parser.add_argument("--installed-tui-smoke", metavar="COMMAND")
    parser.add_argument("--installed-textual-app", metavar="PYTHON")
    parser.add_argument("--cwd", default=None)
    args = parser.parse_args()
    if args.installed_textual_app:
        _assert_installed_textual_app(args.installed_textual_app)
        return 0
    if args.installed_tui_smoke:
        _assert_installed_tui(args.installed_tui_smoke, Path(args.cwd or os.getcwd()))
        print("PASS installed-tui-pseudo-tty")
        return 0
    if args.stdout_redirect:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
        return _run_with_tty_stdin_redirected_stdout(args.stdout_redirect, env)
    if args.self_check:
        root = Path(__file__).resolve().parents[2]
        _assert_interactive(root)
        _assert_delete_confirmation(root)
        print("PASS pty-cli-driver-ready")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
