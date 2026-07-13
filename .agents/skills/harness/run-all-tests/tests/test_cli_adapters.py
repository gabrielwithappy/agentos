# tests/test_cli_adapters.py
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute() / "core-engine"))
from cli_adapters import ClaudeAdapter, GeminiAdapter, CodexAdapter, CLIAdapter
import subprocess


def mock_result(returncode=0, stdout="output", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m

def make_popen_mock(lines: list[str], returncode: int = 0):
    """ClaudeAdapter용 Popen mock (pass-through 라인 시뮬레이션)"""
    mock_proc = MagicMock()
    mock_proc.stdout = iter(line + "\n" for line in lines)
    mock_proc.returncode = returncode
    mock_proc.wait = MagicMock(return_value=returncode)
    return mock_proc

def make_codex_proc(returncode=0, communicate_result=("output", ""), communicate_side_effect=None):
    mock_proc = MagicMock()
    mock_proc.stdin = MagicMock()
    mock_proc.stdin_mock = mock_proc.stdin
    mock_proc.pid = 4321
    mock_proc.returncode = returncode
    mock_proc.poll = MagicMock(return_value=None)
    mock_proc.communicate = MagicMock(return_value=communicate_result)
    if communicate_side_effect is not None:
        mock_proc.communicate.side_effect = communicate_side_effect
    mock_proc.kill = MagicMock()
    return mock_proc


REAL_CODEX_PROCESS_SCRIPT = (
    "import subprocess, sys, time; "
    "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
    "sys.stdin.read(); "
    "time.sleep(30)"
)


def expected_codex_cmd(
    last_message_path: Optional[str] = None,
    mcp_config_args: Optional[list[str]] = None,
) -> list[str]:
    cmd = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "-s",
        "danger-full-access",
        "-c",
        'approval_policy="never"',
    ]
    if mcp_config_args is None:
        cmd.extend(["-c", "mcp_servers={}"])
    else:
        cmd.extend(mcp_config_args)
    if last_message_path is not None:
        cmd.extend(["--output-last-message", last_message_path])
    cmd.append("-")
    return cmd


def wait_for_process_group_exit(pgid: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False

def test_claude_success():
    with patch("subprocess.Popen", return_value=make_popen_mock(["done"])) as mp:
        code, out = ClaudeAdapter().run("test")
        assert code == 0 and "done" in out
        cmd = mp.call_args[0][0]
        assert "claude" in cmd and "--dangerously-skip-permissions" in cmd

def test_claude_nonzero_exit():
    with patch("subprocess.Popen", return_value=make_popen_mock(["output"], returncode=1)):
        code, _ = ClaudeAdapter().run("test")
        assert code == 1

def test_claude_timeout():
    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait = MagicMock(side_effect=subprocess.TimeoutExpired("claude", 300))
    mock_proc.kill = MagicMock()
    with patch("subprocess.Popen", return_value=mock_proc):
        code, out = ClaudeAdapter().run("test")
        assert code == -1
        assert "[TIMEOUT]" in out

def test_claude_not_installed():
    with patch("subprocess.Popen", side_effect=FileNotFoundError()):
        try:
            ClaudeAdapter().run("test")
            assert False, "FileNotFoundError가 전파되어야 함"
        except FileNotFoundError:
            pass

def test_codex_success():
    proc = make_codex_proc(communicate_result=("raw codex out", ""))
    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.run", return_value=mock_result(stdout="usage: codex exec --output-last-message <file>")) as mock_help, \
         patch("subprocess.Popen", return_value=proc) as mock_popen, \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.Path.read_text", return_value="assistant final only"):
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/codex-last-message.txt"
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test")

    assert code == 0
    cmd = mock_popen.call_args.args[0]
    assert cmd == expected_codex_cmd("/tmp/codex-last-message.txt")
    assert mock_popen.call_args.kwargs["start_new_session"] is True
    proc.stdin_mock.write.assert_called_once_with("test")
    proc.stdin_mock.close.assert_called_once()
    assert "[dispatch] completed" in out
    assert "[output_last_message] source=last_message" in out
    assert out.endswith("assistant final only")

def test_codex_prefers_output_last_message():
    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.run", return_value=mock_result(stdout="usage: codex exec --output-last-message <file>")), \
         patch("subprocess.Popen", return_value=make_codex_proc(communicate_result=("raw transcript with <promise>HARNESS_COMPLETE</promise>", "codex warning"))), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.Path.read_text", return_value="assistant final only"):
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/codex-last-message.txt"
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test")

    assert code == 0
    assert "[dispatch] completed" in out
    assert "[output_last_message] source=last_message" in out
    assert out.endswith("assistant final only\n[stderr]\ncodex warning")

def test_codex_falls_back_to_stdout_when_last_message_missing():
    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.run", return_value=mock_result(stdout="usage: codex exec --output-last-message <file>")), \
         patch("subprocess.Popen", return_value=make_codex_proc(communicate_result=("raw transcript with <promise>HARNESS_COMPLETE</promise>", "codex warning"))), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.Path.read_text", return_value=""):
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/codex-last-message.txt"
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test")

    assert code == 0
    assert "[output_last_message] fallback_reason=empty_file" in out
    assert out.endswith("raw transcript with <promise>HARNESS_COMPLETE</promise>\n[stderr]\ncodex warning")

def test_codex_without_output_last_message_support_uses_stdout():
    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch("subprocess.Popen", return_value=make_codex_proc(communicate_result=("codex out", ""))) as mock_popen:
        code, out = CodexAdapter().run("test")

    assert code == 0
    assert "[dispatch] completed" in out
    assert out.endswith("codex out")
    cmd = mock_popen.call_args.args[0]
    assert cmd == expected_codex_cmd()


def test_codex_mcp_free_launch_contract():
    cmd = CodexAdapter._build_launch_contract(Path("/tmp/codex-last-message.txt"))

    assert cmd == expected_codex_cmd("/tmp/codex-last-message.txt")
    assert "--ignore-user-config" in cmd
    assert "--ephemeral" in cmd
    assert cmd.count("-c") == 2
    assert "mcp_servers={}" in cmd
    assert cmd[-1] == "-"


def test_codex_selected_mcp_launch_contract():
    mcp_args = [
        "-c",
        'mcp_servers.penpot.url="http://localhost:4401/mcp"',
        "-c",
        'mcp_servers.stitch.command="bash"',
        "-c",
        'mcp_servers.stitch.args=[".codex/start-stitch-mcp.sh"]',
    ]

    cmd = CodexAdapter._build_launch_contract(
        Path("/tmp/codex-last-message.txt"),
        mcp_args,
    )

    assert cmd == expected_codex_cmd("/tmp/codex-last-message.txt", mcp_args)
    assert "mcp_servers={}" not in cmd
    assert 'mcp_servers.penpot.url="http://localhost:4401/mcp"' in cmd
    assert 'mcp_servers.stitch.command="bash"' in cmd
    assert cmd.count("-c") == 4
    assert cmd[-1] == "-"


def test_codex_configure_mcp_applies_to_run():
    proc = make_codex_proc(communicate_result=("codex out", ""))
    mcp_args = ["-c", 'mcp_servers.penpot.url="http://localhost:4401/mcp"']
    adapter = CodexAdapter()
    adapter.configure_mcp(mcp_args)

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch("subprocess.Popen", return_value=proc) as mock_popen:
        code, out = adapter.run("test")

    assert code == 0
    assert "[dispatch] completed" in out
    assert mock_popen.call_args.args[0] == expected_codex_cmd(mcp_config_args=mcp_args)


def test_codex_stagnation_timeout_default():
    adapter = CodexAdapter()
    assert CodexAdapter.DEFAULT_STAGNATION_TIMEOUT_SECONDS == 60.0
    assert adapter.stagnation_timeout_seconds == 60.0


def test_codex_custom_stagnation_timeout_appears_in_reason(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 7.5, 7.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter(stagnation_timeout_seconds=5).run("test", timeout=120)

    assert code == -2
    assert "[STAGNATION]" in out
    assert "Codex child made no progress for 5s" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)

def test_codex_stagnation_returns_reason(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.run", return_value=mock_result(stdout="usage: codex exec --output-last-message <file>")), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == -2
    assert "[STAGNATION]" in out
    assert "[cleanup] process_group_terminated" in out
    assert "last_message_size=0" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_dispatch_failure_surfaces_phase_and_cleanup():
    proc = make_codex_proc(communicate_result=("partial stdout", "partial stderr"))
    proc.stdin.write.side_effect = BrokenPipeError("stdin closed")

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.os.killpg") as mock_killpg:
        code, out = CodexAdapter().run("test")

    assert code == 124
    assert "dispatch failure" in out
    assert "[cleanup] process_group_terminated" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_completion_after_quiet_returns_success(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("<promise>HARNESS_COMPLETE</promise>", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("<promise>HARNESS_COMPLETE</promise>", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("<promise>HARNESS_COMPLETE</promise>", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == 0
    assert "completion-after-quiet" in out
    assert "[cleanup] process_group_terminated" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_empty_last_message_raw_promise_stays_stagnation(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("검증 명령/결과: pytest => passed\n최종 산출물 경로: x\n마지막 checkpoint 요약: y\n<promise>HARNESS_COMPLETE</promise>", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("검증 명령/결과: pytest => passed\n최종 산출물 경로: x\n마지막 checkpoint 요약: y\n<promise>HARNESS_COMPLETE</promise>", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == -2
    assert "[STAGNATION]" in out
    assert "completion-after-quiet" not in out
    assert "[output_last_message] fallback_reason=empty_file" in out
    assert "[cleanup] process_group_terminated" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_prompt_echo_promise_does_not_promote_quiet_completion(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("prompt echo <promise>HARNESS_COMPLETE</promise>", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("prompt echo <promise>HARNESS_COMPLETE</promise>", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == -2
    assert "[STAGNATION]" in out
    assert "completion-after-quiet" not in out
    assert "<promise>HARNESS_COMPLETE</promise>" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_completion_after_quiet_promotes_last_message_success(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("# AGENTS.md — 행동 운영 지침", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired("codex", 1, output="", stderr="")
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("", "")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("", "")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == 0
    assert "completion-after-quiet" in out
    assert "# AGENTS.md — 행동 운영 지침" in out
    assert "[cleanup] process_group_terminated" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_meaningful_stderr_progress_avoids_false_stagnation(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    proc = make_codex_proc(returncode=0)
    timeout_errors = [
        subprocess.TimeoutExpired("codex", 1, output="", stderr="planner: step 1"),
        subprocess.TimeoutExpired("codex", 1, output="", stderr="planner: step 1\nplanner: step 2"),
    ]

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("done", "planner: step 1\nplanner: step 2")
        if timeout_errors:
            raise timeout_errors.pop(0)
        return ("done", "planner: step 1\nplanner: step 2")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 3.0, 3.5, 4.0, 4.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=30)

    assert code == 0
    assert "[STAGNATION]" not in out


def test_codex_hook_noise_does_not_count_as_progress(tmp_path):
    last_message = tmp_path / "codex-last-message.txt"
    last_message.write_text("", encoding="utf-8")
    timeout_exc = subprocess.TimeoutExpired(
        "codex",
        1,
        output="",
        stderr="hook: SessionStart\nhook: SessionStart Completed\ntokens used\n123",
    )
    proc = make_codex_proc()
    call_count = {"value": 0}

    def communicate_side_effect(*args, **kwargs):
        if "timeout" not in kwargs:
            return ("", "hook: SessionStart\nhook: SessionStart Completed\ntokens used\n123")
        call_count["value"] += 1
        if call_count["value"] <= 2:
            raise timeout_exc
        return ("", "hook: SessionStart\nhook: SessionStart Completed\ntokens used\n123")

    proc.communicate.side_effect = communicate_side_effect
    monotonic_values = iter([0.0, 1.0, 2.0, 61.5, 61.5])

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=True), \
         patch("subprocess.Popen", return_value=proc), \
         patch("cli_adapters.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("cli_adapters.os.killpg") as mock_killpg, \
         patch("cli_adapters.time.monotonic", side_effect=lambda: next(monotonic_values)):
        mock_tmp.return_value.__enter__.return_value.name = str(last_message)
        mock_tmp.return_value.__exit__.return_value = False
        code, out = CodexAdapter().run("test", timeout=120)

    assert code == -2
    assert "[STAGNATION]" in out
    assert "[cleanup] process_group_terminated" in out
    mock_killpg.assert_called_once_with(proc.pid, __import__("signal").SIGKILL)


def test_codex_meaningful_stderr_fingerprint_accepts_bytes():
    fingerprint = CodexAdapter._meaningful_stderr_fingerprint(
        b"hook: SessionStart\nhook: SessionStart Completed\nplanner: step 1\n"
    )

    assert "planner: step 1" in fingerprint
    assert "hook: SessionStart" not in fingerprint


def test_codex_interrupt_cleans_process_group():
    adapter = CodexAdapter()
    real_popen = subprocess.Popen
    spawned: dict[str, object] = {}

    def popen_wrapper(cmd, **kwargs):
        proc = real_popen(cmd, **kwargs)
        spawned["proc"] = proc
        spawned["pgid"] = os.getpgid(proc.pid)
        return proc

    def send_sigint_when_ready() -> None:
        while "pgid" not in spawned:
            time.sleep(0.02)
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGINT)

    sender = __import__("threading").Thread(target=send_sigint_when_ready, daemon=True)
    sender.start()

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch.object(CodexAdapter, "_build_launch_contract", return_value=[sys.executable, "-c", REAL_CODEX_PROCESS_SCRIPT]), \
         patch("cli_adapters.subprocess.Popen", side_effect=popen_wrapper):
        with pytest.raises(KeyboardInterrupt):
            adapter.run("test", timeout=30)

    sender.join(timeout=1)
    assert wait_for_process_group_exit(spawned["pgid"])


def test_codex_signal_termination_cleans_process_group():
    adapter = CodexAdapter()
    real_popen = subprocess.Popen
    spawned: dict[str, object] = {}

    def popen_wrapper(cmd, **kwargs):
        proc = real_popen(cmd, **kwargs)
        spawned["proc"] = proc
        spawned["pgid"] = os.getpgid(proc.pid)
        return proc

    def send_sigterm_when_ready() -> None:
        while "pgid" not in spawned:
            time.sleep(0.02)
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGTERM)

    sender = __import__("threading").Thread(target=send_sigterm_when_ready, daemon=True)
    sender.start()

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch.object(CodexAdapter, "_build_launch_contract", return_value=[sys.executable, "-c", REAL_CODEX_PROCESS_SCRIPT]), \
         patch("cli_adapters.subprocess.Popen", side_effect=popen_wrapper):
        with pytest.raises(SystemExit) as exc_info:
            adapter.run("test", timeout=30)

    sender.join(timeout=1)
    assert exc_info.value.code == 128 + signal.SIGTERM
    assert wait_for_process_group_exit(spawned["pgid"])

def test_detect_cli_order():
    """gemini → claude → codex 탐색 순서"""
    with patch("shutil.which", side_effect=lambda x: "/bin/claude" if x == "claude" else None):
        assert CLIAdapter.detect() == "claude"

def test_detect_cli_none():
    with patch("shutil.which", return_value=None):
        assert CLIAdapter.detect() is None
