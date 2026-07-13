# .agents/skills/harness/core-engine/cli_adapters.py
#
# [fresh-process / context reset 계약]
# 각 CLIAdapter.run() 호출은 독립된 새 subprocess를 생성한다.
# - 이전 호출의 프로세스 메모리나 CLI 세션은 재사용되지 않는다.
# - subprocess.Popen / subprocess.run 으로 매 호출마다 새 프로세스를 만든다.
# - 장기 세션 재사용 또는 숨은 state 공유 경로를 만들지 않는다.
from __future__ import annotations
import os
import tempfile
import re
import shutil
import signal
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class _SignalTermination(Exception):
    def __init__(self, signum: int):
        self.signum = signum
        super().__init__(signum)


class _ProcessSignalGuard:
    def __init__(self, cleanup_callback):
        self._cleanup_callback = cleanup_callback
        self._previous_handlers: dict[int, signal.Handlers] = {}
        self._installed = False

    def __enter__(self) -> "_ProcessSignalGuard":
        if threading.current_thread() is not threading.main_thread():
            return self
        for signum in (signal.SIGINT, signal.SIGTERM):
            self._previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handle_signal)
        self._installed = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._installed:
            return
        for signum, handler in self._previous_handlers.items():
            signal.signal(signum, handler)

    def _handle_signal(self, signum: int, _frame) -> None:
        self._cleanup_callback()
        raise _SignalTermination(signum)


class CLIAdapter(ABC):
    @abstractmethod
    def run(self, prompt: str, timeout: int = 300) -> tuple[int, str]:
        """새 CLI 프로세스를 생성하여 prompt를 실행한다.
        반환: (exit_code, output). timeout 시 (-1, '[TIMEOUT]').
        [계약] 각 호출은 fresh subprocess — 이전 iteration과 컨텍스트를 공유하지 않는다."""
        ...

    def cleanup_active_child(self) -> bool:
        return False

    def configure_mcp(self, mcp_config_args: list[str]) -> None:
        return None

    def configure_stagnation_timeout(self, seconds: float) -> None:
        return None

    @staticmethod
    def detect() -> Optional[str]:
        """gemini → claude → codex 순으로 탐색 (sh detect_cli와 동일 순서)"""
        for name in ("gemini", "claude", "codex"):
            if shutil.which(name):
                return name
        return None

    @staticmethod
    def get(name: str) -> "CLIAdapter":
        adapters: dict[str, type] = {
            "claude": ClaudeAdapter,
            "gemini": GeminiAdapter,
            "codex": CodexAdapter,
        }
        if name not in adapters:
            raise ValueError(f"알 수 없는 CLI: {name}")
        return adapters[name]()


def _run(cmd: list[str], timeout: int, input_text: str | None = None) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return -1, "[TIMEOUT] CLI 응답 시간 초과"
    # FileNotFoundError는 의도적으로 전파 (CLI 미설치)


def _merge_output(stdout: str, stderr: str) -> str:
    output = stdout
    if stderr:
        output += "\n[stderr]\n" + stderr
    return output


class ClaudeAdapter(CLIAdapter):
    def run(self, prompt: str, timeout: int = 300) -> tuple[int, str]:
        cmd = ["claude", "--dangerously-skip-permissions", "-p", prompt]
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            output_parts: list[str] = []
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="", flush=True)
                output_parts.append(line)
            proc.wait(timeout=timeout)
            return proc.returncode, "".join(output_parts)
        except subprocess.TimeoutExpired:
            proc.kill()
            return -1, "[TIMEOUT] CLI 응답 시간 초과"


class GeminiAdapter(CLIAdapter):
    def run(self, prompt: str, timeout: int = 300) -> tuple[int, str]:
        # gemini -p 플래그 지원 여부 확인 (sh의 grep -qE '\-p|--prompt'와 동일)
        help_result = subprocess.run(
            ["gemini", "--help"], capture_output=True, text=True
        )
        if re.search(r'-p|--prompt', help_result.stdout + help_result.stderr):
            return _run(["gemini", "-p", prompt], timeout)
        else:
            # stdin 방식 fallback
            try:
                result = subprocess.run(
                    ["gemini"], input=prompt, capture_output=True,
                    text=True, timeout=timeout
                )
                return result.returncode, result.stdout
            except subprocess.TimeoutExpired:
                return -1, "[TIMEOUT] CLI 응답 시간 초과"


class CodexAdapter(CLIAdapter):
    _output_last_message_supported: Optional[bool] = None
    POLL_INTERVAL_SECONDS = 1.0
    DEFAULT_STAGNATION_TIMEOUT_SECONDS = 60.0
    CODEX_SANDBOX_MODE = "danger-full-access"
    CODEX_APPROVAL_POLICY = 'approval_policy="never"'
    CODEX_MCP_SERVERS_CONFIG = "mcp_servers={}"
    PHASE_LAUNCH = "launch"
    PHASE_DISPATCH = "dispatch"
    PHASE_OUTPUT_LAST_MESSAGE = "output_last_message"
    PHASE_STAGNATION = "stagnation"
    PHASE_COMPLETION_AFTER_QUIET = "completion-after-quiet"
    STDERR_NOISE_PATTERNS = (
        re.compile(r"^OpenAI Codex v", re.IGNORECASE),
        re.compile(r"^-{2,}$"),
        re.compile(r"^workdir:\s*", re.IGNORECASE),
        re.compile(r"^model:\s*", re.IGNORECASE),
        re.compile(r"^provider:\s*", re.IGNORECASE),
        re.compile(r"^approval:\s*", re.IGNORECASE),
        re.compile(r"^sandbox:\s*", re.IGNORECASE),
        re.compile(r"^reasoning effort:\s*", re.IGNORECASE),
        re.compile(r"^session id:\s*", re.IGNORECASE),
        re.compile(r"^hook:\s*", re.IGNORECASE),
        re.compile(r"^tokens used\s*$", re.IGNORECASE),
        re.compile(r"^[0-9][0-9,]*$"),
    )

    def __init__(
        self,
        mcp_config_args: list[str] | None = None,
        stagnation_timeout_seconds: float = DEFAULT_STAGNATION_TIMEOUT_SECONDS,
    ) -> None:
        self._active_proc: subprocess.Popen[str] | None = None
        self._mcp_config_args = list(mcp_config_args) if mcp_config_args is not None else None
        self.configure_stagnation_timeout(stagnation_timeout_seconds)

    def configure_mcp(self, mcp_config_args: list[str]) -> None:
        self._mcp_config_args = list(mcp_config_args)

    def configure_stagnation_timeout(self, seconds: float) -> None:
        if seconds <= 0:
            raise ValueError("stagnation_timeout_seconds must be > 0")
        self.stagnation_timeout_seconds = float(seconds)

    @classmethod
    def _build_launch_contract(
        cls,
        last_message_path: Path | None,
        mcp_config_args: list[str] | None = None,
    ) -> list[str]:
        # codex exec launch contract: isolated session, selected MCP only, stdin dispatch.
        cmd = [
            "codex",
            "exec",
            "--ignore-user-config",
            "--ephemeral",
            "-s",
            cls.CODEX_SANDBOX_MODE,
            "-c",
            cls.CODEX_APPROVAL_POLICY,
        ]
        if mcp_config_args is None:
            cmd.extend(["-c", cls.CODEX_MCP_SERVERS_CONFIG])
        else:
            cmd.extend(mcp_config_args)
        if last_message_path is not None:
            cmd.extend(["--output-last-message", str(last_message_path)])
        cmd.append("-")
        return cmd

    @classmethod
    def _phase_prefix(cls, phase: str, detail: str) -> str:
        return f"[{phase}] {detail}"

    @staticmethod
    def _cleanup_path(path: Path | None) -> None:
        if path is None:
            return
        try:
            path.unlink()
        except OSError:
            pass

    def cleanup_active_child(self) -> bool:
        proc = self._active_proc
        if proc is None:
            return False
        self._terminate_process_group(proc)
        return True

    @staticmethod
    def _terminate_process_group(proc: subprocess.Popen[str]) -> None:
        poll = getattr(proc, "poll", None)
        if callable(poll):
            try:
                if poll() is not None:
                    return
            except Exception:
                pass

        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            proc.kill()

    @classmethod
    def _supports_output_last_message(cls) -> bool:
        if cls._output_last_message_supported is not None:
            return cls._output_last_message_supported

        help_result = subprocess.run(
            ["codex", "exec", "--help"],
            capture_output=True,
            text=True,
        )
        cls._output_last_message_supported = "--output-last-message" in (
            help_result.stdout + help_result.stderr
        )
        return cls._output_last_message_supported

    @staticmethod
    def _last_message_size(path: Path | None) -> int:
        if path is None:
            return -1
        try:
            return path.stat().st_size
        except OSError:
            return -1

    @staticmethod
    def _finalize_codex_output(stdout: str, stderr: str, last_message_path: Path | None) -> tuple[str, str]:
        output = _merge_output(stdout, stderr)
        if last_message_path is None:
            return output, ""

        try:
            last_message = last_message_path.read_text(encoding="utf-8").strip()
        except OSError:
            return output, "[output_last_message] fallback_reason=missing_file"
        finally:
            try:
                last_message_path.unlink()
            except OSError:
                pass

        if not last_message:
            return output, "[output_last_message] fallback_reason=empty_file"
        return _merge_output(last_message, stderr), "[output_last_message] source=last_message"

    @classmethod
    def _meaningful_stderr_fingerprint(cls, stderr: str | bytes | None) -> str:
        if stderr is None:
            normalized = ""
        elif isinstance(stderr, bytes):
            normalized = stderr.decode("utf-8", errors="replace")
        else:
            normalized = stderr
        meaningful_lines: list[str] = []
        for raw_line in normalized.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if any(pattern.search(line) for pattern in cls.STDERR_NOISE_PATTERNS):
                continue
            meaningful_lines.append(line)
        return "\n".join(meaningful_lines)

    @classmethod
    def _should_promote_quiet_completion(
        cls,
        output: str,
        output_last_message_reason: str,
    ) -> bool:
        return output_last_message_reason == "[output_last_message] source=last_message"

    def run(self, prompt: str, timeout: int = 300) -> tuple[int, str]:
        last_message_path: Path | None = None
        if self._supports_output_last_message():
            with tempfile.NamedTemporaryFile(
                prefix="codex-last-message-",
                suffix=".txt",
                delete=False,
            ) as temp_file:
                last_message_path = Path(temp_file.name)
        cmd = self._build_launch_contract(last_message_path, self._mcp_config_args)

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except FileNotFoundError:
            self._cleanup_path(last_message_path)
            raise
        except OSError as exc:
            self._cleanup_path(last_message_path)
            reason = self._phase_prefix(self.PHASE_LAUNCH, f"launch failure: {exc}")
            return 125, reason

        self._active_proc = proc
        try:
            with _ProcessSignalGuard(self.cleanup_active_child):
                try:
                    assert proc.stdin is not None
                    proc.stdin.write(prompt)
                    proc.stdin.close()
                    proc.stdin = None
                except (BrokenPipeError, OSError, ValueError) as exc:
                    self._terminate_process_group(proc)
                    final_stdout, final_stderr = proc.communicate()
                    reason = self._phase_prefix(self.PHASE_DISPATCH, f"dispatch failure: {exc}")
                    return 124, "\n".join(
                        [
                            reason,
                            "[cleanup] process_group_terminated",
                            _merge_output(final_stdout or "", final_stderr or ""),
                        ]
                    ).strip()

                stdout_text = ""
                stderr_text = ""
                last_stdout_len = 0
                last_stderr_fingerprint = ""
                last_message_size = self._last_message_size(last_message_path)
                started_at = time.monotonic()
                last_progress_at = started_at

                while True:
                    elapsed = time.monotonic() - started_at
                    if elapsed >= timeout:
                        self._terminate_process_group(proc)
                        final_stdout, final_stderr = proc.communicate()
                        stdout_text = final_stdout or stdout_text
                        stderr_text = final_stderr or stderr_text
                        output, output_last_message_reason = self._finalize_codex_output(
                            stdout_text,
                            stderr_text,
                            last_message_path,
                        )
                        timeout_reason = self._phase_prefix(self.PHASE_DISPATCH, "timeout")
                        return -1, "\n".join(
                            part for part in [
                                timeout_reason,
                                "[cleanup] process_group_terminated",
                                output_last_message_reason,
                                output,
                                "[stderr]\n[TIMEOUT] CLI 응답 시간 초과",
                            ] if part
                        )

                    wait_window = min(self.POLL_INTERVAL_SECONDS, timeout - elapsed)
                    try:
                        final_stdout, final_stderr = proc.communicate(timeout=max(wait_window, 0.01))
                        stdout_text = final_stdout or ""
                        stderr_text = final_stderr or ""
                        output, output_last_message_reason = self._finalize_codex_output(
                            stdout_text,
                            stderr_text,
                            last_message_path,
                        )
                        phase_label = self._phase_prefix(self.PHASE_DISPATCH, "completed")
                        return proc.returncode, "\n".join(
                            part for part in [phase_label, output_last_message_reason, output] if part
                        )
                    except subprocess.TimeoutExpired as exc:
                        stdout_text = exc.stdout or ""
                        stderr_text = exc.stderr or ""

                    current_message_size = self._last_message_size(last_message_path)
                    current_stderr_fingerprint = self._meaningful_stderr_fingerprint(stderr_text)
                    progressed = (
                        len(stdout_text) != last_stdout_len
                        or current_message_size != last_message_size
                        or current_stderr_fingerprint != last_stderr_fingerprint
                    )
                    if progressed:
                        last_progress_at = time.monotonic()
                        last_stdout_len = len(stdout_text)
                        last_stderr_fingerprint = current_stderr_fingerprint
                        last_message_size = current_message_size
                        continue

                    stagnation_elapsed = time.monotonic() - last_progress_at
                    if stagnation_elapsed >= self.stagnation_timeout_seconds:
                        self._terminate_process_group(proc)
                        final_stdout, final_stderr = proc.communicate()
                        stdout_text = final_stdout or stdout_text
                        stderr_text = final_stderr or stderr_text
                        output, output_last_message_reason = self._finalize_codex_output(
                            stdout_text,
                            stderr_text,
                            last_message_path,
                        )
                        reason = (
                            f"[STAGNATION] {self.PHASE_STAGNATION} Codex child made no progress for "
                            f"{int(self.stagnation_timeout_seconds)}s | "
                            f"stdout_chars={len(stdout_text)} stderr_chars={len(stderr_text)} "
                            f"last_message_size={current_message_size}"
                        )
                        if self._should_promote_quiet_completion(output, output_last_message_reason):
                            completion_reason = self._phase_prefix(
                                self.PHASE_COMPLETION_AFTER_QUIET,
                                "completion-after-quiet last-message output detected before stagnation closeout",
                            )
                            return 0, "\n".join(
                                part for part in [
                                    completion_reason,
                                    "[cleanup] process_group_terminated",
                                    output_last_message_reason,
                                    output,
                                ] if part
                            )
                        if output:
                            return -2, "\n".join(
                                part for part in [
                                    reason,
                                    "[cleanup] process_group_terminated",
                                    output_last_message_reason,
                                    output,
                                ] if part
                            )
                        return -2, "\n".join([reason, "[cleanup] process_group_terminated"])
        except _SignalTermination as exc:
            self.cleanup_active_child()
            try:
                proc.communicate(timeout=1)
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass
            if exc.signum == signal.SIGINT:
                raise KeyboardInterrupt
            raise SystemExit(128 + exc.signum)
        except BaseException:
            self.cleanup_active_child()
            try:
                proc.communicate(timeout=1)
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass
            raise
        finally:
            self._active_proc = None
            self._cleanup_path(last_message_path)
