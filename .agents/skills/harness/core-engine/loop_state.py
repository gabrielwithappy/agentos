# .agents/harness/loop_state.py
from __future__ import annotations
import fcntl
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone


@dataclass
class LoopState:
    active: bool = True
    execution_locked: bool = False
    iteration: int = 1
    max_iterations: int = 30
    completion_promise: str = "HARNESS_COMPLETE"
    cli: str = "auto"
    harness_version: str = "1.0"
    loop_id: str = ""
    started_at: str = ""
    last_run: str = "null"
    last_checkpoint_at: str = "null"
    last_event: str = ""
    current_phase: str = ""
    current_task: str = ""
    current_step: str = ""
    plan_path: str = ""
    mcp_servers: str = "[]"
    prompt_summary: str = ""
    result_summary: str = ""
    outcome_code: str = ""
    failure_class: str = ""
    status_hint: str = ""
    blocked_reason: str = ""
    stop_reason: str = ""
    pending_escalation_id: str = ""
    pending_escalation_summary: str = ""
    pending_override_response: str = ""
    prompt: str = ""

    @staticmethod
    def _clean_scalar(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', "'").strip()

    @classmethod
    def _format_block(cls, key: str, value: str) -> str:
        lines = value.splitlines() or [value]
        rendered = "\n".join(f"  {line}" for line in lines if line is not None)
        if not rendered:
            return f"{key}: |\n"
        return f"{key}: |\n{rendered}\n"

    def to_file(self, path: Path) -> None:
        frontmatter_lines = [
            "---",
            f"active: {str(self.active).lower()}",
            f"execution_locked: {str(self.execution_locked).lower()}",
            f"iteration: {self.iteration}",
            f"max_iterations: {self.max_iterations}",
            f'completion_promise: "{self._clean_scalar(self.completion_promise)}"',
            f"cli: {self.cli}",
            f'harness_version: "{self._clean_scalar(self.harness_version)}"',
            f'loop_id: "{self._clean_scalar(self.loop_id)}"',
            f'started_at: "{self.started_at}"',
            f"last_run: {self.last_run}",
            f"last_checkpoint_at: {self.last_checkpoint_at}",
        ]
        for key, value in (
            ("last_event", self.last_event),
            ("current_phase", self.current_phase),
            ("current_task", self.current_task),
            ("current_step", self.current_step),
            ("plan_path", self.plan_path),
            ("mcp_servers", self.mcp_servers),
            ("prompt_summary", self.prompt_summary),
            ("result_summary", self.result_summary),
            ("outcome_code", self.outcome_code),
            ("failure_class", self.failure_class),
            ("status_hint", self.status_hint),
            ("blocked_reason", self.blocked_reason),
            ("stop_reason", self.stop_reason),
            ("pending_escalation_id", self.pending_escalation_id),
            ("pending_escalation_summary", self.pending_escalation_summary),
            ("pending_override_response", self.pending_override_response),
        ):
            frontmatter_lines.append(self._format_block(key, value).rstrip("\n"))
        text = "\n".join(frontmatter_lines) + "\n---\n\n" + f"{self.prompt}\n"
        lock_path = path.with_suffix(path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("w", encoding="utf-8") as lock_fh:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
            path.write_text(text, encoding="utf-8")
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

    @classmethod
    def from_file(cls, path: Path) -> "LoopState":
        text = path.read_text(encoding="utf-8")
        # "---\n" 기준으로 분리 (sh의 sed '/^---$/,/^---$/' 동작과 동일)
        parts = text.split("---\n", 2)
        fm = parts[1] if len(parts) >= 2 else ""
        body = parts[2].strip() if len(parts) >= 3 else ""
        fm_lines = fm.splitlines()

        def get(key: str, default: str = "") -> str:
            inline_re = re.compile(rf'^{re.escape(key)}:\s*"?([^"\n]*)"?\s*$')
            block_header = f"{key}: |"
            for idx, line in enumerate(fm_lines):
                if line == block_header:
                    collected: list[str] = []
                    for block_line in fm_lines[idx + 1:]:
                        if block_line.startswith("  "):
                            collected.append(block_line[2:])
                            continue
                        if not block_line:
                            collected.append("")
                            continue
                        break
                    return "\n".join(collected).rstrip()
                match = inline_re.match(line)
                if match:
                    return match.group(1).strip()
            return default

        return cls(
            active=get("active", "true") == "true",
            execution_locked=get("execution_locked", "false") == "true",
            iteration=int(get("iteration", "1")),
            max_iterations=int(get("max_iterations", "30")),
            completion_promise=get("completion_promise", "HARNESS_COMPLETE"),
            cli=get("cli", "auto"),
            harness_version=get("harness_version", "1.0"),
            loop_id=get("loop_id", ""),
            started_at=get("started_at", ""),
            last_run=get("last_run", "null"),
            last_checkpoint_at=get("last_checkpoint_at", "null"),
            last_event=get("last_event", ""),
            current_phase=get("current_phase", ""),
            current_task=get("current_task", ""),
            current_step=get("current_step", ""),
            plan_path=get("plan_path", ""),
            mcp_servers=get("mcp_servers", "[]"),
            prompt_summary=get("prompt_summary", ""),
            result_summary=get("result_summary", ""),
            outcome_code=get("outcome_code", ""),
            failure_class=get("failure_class", ""),
            status_hint=get("status_hint", ""),
            blocked_reason=get("blocked_reason", ""),
            stop_reason=get("stop_reason", ""),
            pending_escalation_id=get("pending_escalation_id", ""),
            pending_escalation_summary=get("pending_escalation_summary", ""),
            pending_override_response=get("pending_override_response", ""),
            prompt=body,
        )

    def bump_iteration(self) -> None:
        self.iteration += 1
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.last_run = f'"{now}"'

    def deactivate(self, path: Path) -> None:
        """비정상 종료 시: active: false 갱신 후 파일 유지"""
        self.active = False
        self.to_file(path)

    @staticmethod
    def delete(path: Path) -> None:
        """정상 완료 시: 파일 삭제 (sh rm -f "$STATE_FILE"과 동일)"""
        path.unlink(missing_ok=True)
