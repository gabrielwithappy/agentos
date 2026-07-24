from __future__ import annotations

import json
import re
import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from agentos.llm.redaction import redact_text, sanitize
from agentos.llm.types import LLMEvent, ProviderStatus


CODEX_MODE = "account-login"
CODEX_RECOVERY_LOGIN = "Run: agentos llm login --provider codex or codex login"
CODEX_RECOVERY_INSTALL = "Install Codex CLI, then run: codex login"

_URL_RE = re.compile(r"https?://[^\s\"\'<>]+")


def _first_url(text: str) -> str | None:
    match = _URL_RE.search(text)
    return match.group(0) if match else None


_ENV_ALLOWLIST = {
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "NO_COLOR",
    "PATH",
    "SHELL",
    "SSL_CERT_FILE",
    "TERM",
    "TMPDIR",
    "USER",
}


class CodexCliProvider:
    """External CLI compatibility path. This is a recovery-only debug/rollback
    provider, selected explicitly via `--provider codex-cli`; it is never the
    default `codex` interactive path."""

    name = "codex-cli"
    mode = CODEX_MODE

    def __init__(self, executable: str | None = None, timeout_seconds: int = 120):
        self._configured_executable = executable
        self.timeout_seconds = timeout_seconds

    def status(self) -> ProviderStatus:
        executable = self._resolve_executable()
        if executable is None:
            return self._missing_cli_status(
                "Codex CLI executable is not available. Install Codex CLI before using provider 'codex'."
            )

        result = self._run_codex(["login", "status"], executable=executable)
        if result.returncode == 0:
            return ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=True,
                authenticated=True,
                persistent_credential=True,
                status="authenticated",
                message="Codex CLI reports an authenticated account-login session.",
            )

        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="unauthenticated",
            message="Codex CLI is installed, but no authenticated account-login session is active.",
            recovery=CODEX_RECOVERY_LOGIN,
            next_command="agentos llm login --provider codex",
        )

    def login(self) -> ProviderStatus:
        executable = self._resolve_executable()
        if executable is None:
            return self._missing_cli_status(
                "Codex CLI executable is not available. Install Codex CLI before logging in."
            )

        result = self._run_codex(["login"], executable=executable)
        return self._login_result(result)

    def login_updates(self) -> Iterator[dict[str, Any]]:
        executable = self._resolve_executable()
        if executable is None:
            yield {"type": "result", "payload": self._missing_cli_status(
                "Codex CLI executable is not available. Install Codex CLI before logging in."
            ).to_dict()}
            return

        try:
            process = subprocess.Popen(
                [executable, "login"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self._subprocess_env(),
                text=True,
            )
        except OSError:
            yield {"type": "result", "payload": self._missing_cli_status(
                "Codex CLI executable is not available. Install Codex CLI before logging in."
            ).to_dict()}
            return

        seen_urls: set[str] = set()
        combined_output: list[str] = []
        assert process.stdout is not None
        for raw_line in process.stdout:
            line = redact_text(raw_line.strip())
            if not line:
                continue
            combined_output.append(line)
            url = _first_url(line)
            if url and url not in seen_urls:
                seen_urls.add(url)
                yield {
                    "type": "hint",
                    "text": f"Open this login URL if the browser did not open:\n{url}",
                }

        returncode = process.wait(timeout=self.timeout_seconds)
        result = subprocess.CompletedProcess(
            [executable, "login"],
            returncode,
            "\n".join(combined_output),
            "",
        )
        yield {"type": "result", "payload": self._login_result(result).to_dict()}

    def _login_result(self, result: subprocess.CompletedProcess[str]) -> ProviderStatus:
        login_url = _first_url(redact_text((result.stdout or "") + "\n" + (result.stderr or "")))
        if result.returncode == 0:
            status = self.status()
            recovery = None if status.authenticated else CODEX_RECOVERY_LOGIN
            if login_url and not status.authenticated:
                recovery = f"Open this login URL if needed: {login_url}\n{CODEX_RECOVERY_LOGIN}"
            return ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=status.credential_present,
                authenticated=status.authenticated,
                persistent_credential=status.persistent_credential,
                status="authenticated" if status.authenticated else "unauthenticated",
                message="Codex CLI login completed. Account-login session is managed by Codex CLI.",
                recovery=recovery,
                next_command=None if status.authenticated else "agentos llm login --provider codex",
            )

        recovery = CODEX_RECOVERY_LOGIN
        if login_url:
            recovery = f"Open this login URL if needed: {login_url}\n{CODEX_RECOVERY_LOGIN}"
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="failed",
            message="Codex CLI login did not complete successfully.",
            recovery=recovery,
            next_command="agentos llm login --provider codex",
        )

    def logout(self) -> ProviderStatus:
        executable = self._resolve_executable()
        if executable is None:
            return self._missing_cli_status(
                "Codex CLI executable is not available. Install Codex CLI before logging out."
            )

        result = self._run_codex(["logout"], executable=executable)
        if result.returncode == 0:
            return ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=False,
                authenticated=False,
                persistent_credential=False,
                status="logged_out",
                message="Codex CLI logout completed. AgentOS did not read or store credentials.",
                next_command="codex login",
            )

        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="failed",
            message="Codex CLI logout did not complete successfully.",
            recovery="Run: codex logout",
            next_command="codex logout",
        )

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]:
        executable = self._resolve_executable()
        if executable is None:
            yield self._error_event(
                code="missing_cli",
                message="Codex CLI executable is not available. Install Codex CLI before using provider 'codex'.",
                recovery=CODEX_RECOVERY_INSTALL,
                retryable=False,
            )
            return

        command = [executable, "exec", "--json", prompt]
        process = self._open_codex_process(["exec", "--json", prompt], executable=executable)
        if process is None:
            yield self._error_event(
                code="missing_cli",
                message="Codex CLI executable is not available. Install Codex CLI before using provider 'codex'.",
                recovery=CODEX_RECOVERY_INSTALL,
                retryable=False,
            )
            return

        stdout_lines: list[str] = []
        buffered_plaintext: list[str] = []
        output_chars = 0
        start_emitted = False

        def emit_start() -> LLMEvent:
            return LLMEvent(
                type="start",
                provider=self.name,
                mode=self.mode,
                metadata={"transport": "codex-cli"},
            )

        assert process.stdout is not None
        for raw_line in process.stdout:
            stdout_lines.append(raw_line.rstrip("\n"))
            stripped = raw_line.strip()
            if stripped.startswith("{"):
                classified = self._parse_output_items(raw_line)
                if classified and not start_emitted:
                    start_emitted = True
                    yield emit_start()
                for kind, text, metadata in classified:
                    if kind == "message_delta":
                        output_chars += len(text or "")
                    yield LLMEvent(
                        type=kind,
                        provider=self.name,
                        mode=self.mode,
                        text=text,
                        metadata=metadata or {},
                    )
            elif stripped and not self._is_diagnostic_line(redact_text(stripped)):
                buffered_plaintext.append(stripped)

        result = self._completed_process_from_stream(
            process=process,
            command=command,
            stdout_lines=stdout_lines,
        )
        if result.returncode != 0:
            code = "codex_cli_timeout" if result.returncode == 124 else "codex_cli_failed"
            message = (
                "Codex CLI timed out."
                if result.returncode == 124
                else "Codex CLI one-shot run did not complete successfully."
            )
            yield self._error_event(
                code=code,
                message=message,
                recovery=CODEX_RECOVERY_LOGIN,
                retryable=True,
            )
            return

        if buffered_plaintext and not start_emitted:
            start_emitted = True
            yield emit_start()

        for raw_text in buffered_plaintext:
            text = str(sanitize(redact_text(raw_text)))
            if not text:
                continue
            output_chars += len(text)
            yield LLMEvent(
                type="message_delta",
                provider=self.name,
                mode=self.mode,
                text=text,
            )

        if not start_emitted:
            yield emit_start()

        yield LLMEvent(
            type="done",
            provider=self.name,
            mode=self.mode,
            usage={
                "input_chars": len(redact_text(prompt)),
                "output_chars": output_chars,
            },
        )

    def _resolve_executable(self) -> str | None:
        configured = self._configured_executable or os.environ.get("CODEX_CLI_PATH")
        if configured:
            candidate = Path(configured)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
            return None
        return shutil.which("codex")

    def _run_codex(self, args: list[str], executable: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [executable, *args],
                check=False,
                capture_output=True,
                env=self._subprocess_env(),
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess([executable, *args], 124, "", "timeout")
        except OSError:
            return subprocess.CompletedProcess([executable, *args], 127, "", "unavailable")

    def _open_codex_process(
        self, args: list[str], *, executable: str
    ) -> subprocess.Popen[str] | None:
        try:
            return subprocess.Popen(
                [executable, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self._subprocess_env(),
                text=True,
            )
        except OSError:
            return None

    def _completed_process_from_stream(
        self,
        *,
        process: subprocess.Popen[str],
        command: list[str],
        stdout_lines: list[str],
    ) -> subprocess.CompletedProcess[str]:
        try:
            returncode = process.wait(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                remaining_stdout, _ = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                remaining_stdout = ""
            if remaining_stdout:
                stdout_lines.extend(remaining_stdout.splitlines())
            return subprocess.CompletedProcess(command, 124, "\n".join(stdout_lines), "timeout")

        return subprocess.CompletedProcess(command, returncode, "\n".join(stdout_lines), "")

    def _subprocess_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        for key in _ENV_ALLOWLIST:
            value = os.environ.get(key)
            if value is not None:
                env[key] = value
        return env

    def _missing_cli_status(self, message: str) -> ProviderStatus:
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="missing_cli",
            message=message,
            recovery=CODEX_RECOVERY_INSTALL,
            next_command="codex login",
        )

    def _error_event(
        self,
        *,
        code: str,
        message: str,
        recovery: str,
        retryable: bool,
    ) -> LLMEvent:
        return LLMEvent(
            type="error",
            provider=self.name,
            mode=self.mode,
            error={"code": code, "message": message},
            recovery=recovery,
            metadata={"retryable": retryable},
        )

    def _parse_output_items(
        self, stdout: str
    ) -> list[tuple[str, str | None, dict[str, Any] | None]]:
        items: list[tuple[str, str | None, dict[str, Any] | None]] = []
        for raw_line in stdout.splitlines():
            line = redact_text(raw_line.strip())
            if not line:
                continue
            if line.startswith("{"):
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    payload = None
                if payload is not None:
                    classified = [
                        entry
                        for entry in (self._classify_item(item) for item in self._iter_items(payload))
                        if entry
                    ]
                    if classified:
                        items.extend(classified)
                    else:
                        text = self._find_text(payload)
                        if text:
                            items.append(("message_delta", redact_text(text), None))
                    continue
            if not self._is_diagnostic_line(line):
                items.append(("message_delta", line, None))
        return [
            (kind, str(sanitize(text)) if text is not None else None, sanitize(metadata) if metadata is not None else None)
            for kind, text, metadata in items
        ]

    def _iter_items(self, value: Any) -> Iterator[dict[str, Any]]:
        if isinstance(value, dict):
            item = value.get("item")
            if isinstance(item, dict):
                yield item
            for nested in value.values():
                yield from self._iter_items(nested)
        elif isinstance(value, list):
            for entry in value:
                yield from self._iter_items(entry)

    def _classify_item(
        self, item: dict[str, Any]
    ) -> tuple[str, str | None, dict[str, Any] | None] | None:
        item_type = item.get("type")
        if item_type == "agent_message":
            text = self._find_text(item.get("text"))
            return ("message_delta", text, None) if text else None
        if item_type == "reasoning":
            text = self._find_text(item.get("text")) or self._find_text(item.get("summary"))
            return ("reasoning", text, None) if text else None
        if item_type in ("function_call", "local_shell_call", "custom_tool_call"):
            name = item.get("name") or item_type
            arguments = item.get("arguments")
            if arguments is None and item_type == "local_shell_call":
                arguments = item.get("command")
            return ("tool_call", None, {"name": name, "arguments": arguments})
        if item_type in ("function_call_output", "local_shell_call_output", "custom_tool_call_output"):
            summary = self._find_text(item.get("output")) or self._find_text(item.get("result"))
            return ("tool_result", None, {"summary": summary or ""})
        return None

    def _find_text(self, value: Any) -> str | None:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = [self._find_text(item) for item in value]
            joined = "".join(part for part in parts if part)
            return joined or None
        if not isinstance(value, dict):
            return None

        item = value.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message":
            text = self._find_text(item.get("text"))
            if text:
                return text

        for key in ("text", "delta", "content", "message", "output"):
            if key in value:
                text = self._find_text(value[key])
                if text:
                    return text
        return None

    def _is_diagnostic_line(self, line: str) -> bool:
        return (
            line == "Reading additional input from stdin..."
            or " WARN " in line
            or line.startswith("WARN ")
        )
