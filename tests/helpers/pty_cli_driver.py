#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pty
import select
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
                prompt_markers = (b"agentos[", b"[y/N]:")
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


def _assert_interactive(root: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentos-pty-"))
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        env["AGENTOS_HOME"] = str(tmp / "home")
        python = str(root / ".venv" / "bin" / "python") if (root / ".venv" / "bin" / "python").exists() else sys.executable
        code, transcript = _run_pty(
            [python, "-m", "agentos.cli", "run"],
            [b"/help\n", b"/session\n", b"/hooks\n", b"/bogus\n", b"hello\n", b"/exit\n"],
            env,
        )
        assert code == 0, transcript
        assert "/help /status /session" in transcript
        assert "Usage: /session list | show <id> | resume <id>" in transcript
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
    args = parser.parse_args()
    if args.self_check:
        root = Path(__file__).resolve().parents[2]
        _assert_interactive(root)
        _assert_delete_confirmation(root)
        print("PASS pty-cli-driver-ready")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
