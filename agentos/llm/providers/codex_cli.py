from __future__ import annotations

import json
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
    name = "codex"
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
        if result.returncode == 0:
            status = self.status()
            return ProviderStatus(
                provider=self.name,
                mode=self.mode,
                credential_present=status.credential_present,
                authenticated=status.authenticated,
                persistent_credential=status.persistent_credential,
                status="authenticated" if status.authenticated else "unauthenticated",
                message="Codex CLI login completed. Account-login session is managed by Codex CLI.",
                recovery=None if status.authenticated else CODEX_RECOVERY_LOGIN,
                next_command=None if status.authenticated else "agentos llm login --provider codex",
            )

        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            status="failed",
            message="Codex CLI login did not complete successfully.",
            recovery=CODEX_RECOVERY_LOGIN,
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

        result = self._run_codex(["exec", "--json", prompt], executable=executable)
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

        yield LLMEvent(
            type="start",
            provider=self.name,
            mode=self.mode,
            metadata={"transport": "codex-cli"},
        )

        output_chars = 0
        for text in self._parse_output_events(result.stdout):
            output_chars += len(text)
            yield LLMEvent(
                type="message_delta",
                provider=self.name,
                mode=self.mode,
                text=text,
            )
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

    def _parse_output_events(self, stdout: str) -> list[str]:
        texts: list[str] = []
        for raw_line in stdout.splitlines():
            line = redact_text(raw_line.strip())
            if not line:
                continue
            text = self._text_from_json_line(line)
            if text:
                texts.append(text)
            elif not line.startswith("{") and not self._is_diagnostic_line(line):
                texts.append(line)
        return [str(sanitize(text)) for text in texts]

    def _text_from_json_line(self, line: str) -> str | None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        text = self._find_text(payload)
        if text:
            return redact_text(text)
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
