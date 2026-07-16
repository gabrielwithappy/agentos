# .agents/skills/harness/core-engine/harness_loop.py
#
# [fresh-process / context reset 계약]
# 각 iteration은 CLIAdapter.run()을 통해 새 CLI 프로세스를 호출한다.
# 프로세스 간 컨텍스트는 공유되지 않으며, 이전 iteration의 메모리·상태가
# 다음 iteration으로 누수되지 않는다 (context reset 보장).
#
# 불변식:
#   - adapter.run()은 매 iteration마다 새 subprocess를 생성한다.
#   - loop-state.md 파일이 유일한 iteration 간 공유 상태다.
#   - HarnessLoop 인스턴스 자체는 제어 엔진이며 에이전트 메모리를 갖지 않는다.
import argparse
import gzip
import hashlib
import json
import re
import signal
import subprocess
import sys
import threading
import time
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone

from loop_state import LoopState
from cli_adapters import CLIAdapter

ESCALATION_RE = re.compile(
    r'(?m)^(?:\s{0,3}(?:#+\s+)?)?(?:\[[^\]]+\]\s+)?\[ESCALATION\]\s*(.+)?$',
    re.IGNORECASE,
)
PROMISE_RE = re.compile(r'<promise>(.*?)</promise>', re.DOTALL)
# AGENTS.md §3.2: heartbeat_interval=5
HEARTBEAT_INTERVAL = 5
CHILD_PROGRESS_POLL_SECONDS = 1.0
CHILD_PROGRESS_HEARTBEAT_SECONDS = 5.0
LOOP_CONFIG_FILE = ".harness-loop.json"
PLAN_PATH_RE = re.compile(r"(.agentos/project/exec-plans/[^\s\"']+\.md)")
ACTIVE_PLAN_PATH_RE = re.compile(r"(.agentos/project/exec-plans/active/[^\s\"']+\.md)")
EXECUTION_CONTRACT_RE = re.compile(
    r"\[EXECUTION_CONTRACT\]\s*(?P<body>.*?)\s*\[/EXECUTION_CONTRACT\]",
    re.DOTALL,
)
EXECUTION_CONTRACT_FIELDS = ["Goal", "Scope", "Actions", "Verification", "Done When"]
REVIEWED_RE = re.compile(r"^> reviewed: true$", re.MULTILINE)
MCP_SERVERS_RE = re.compile(r"^>\s*mcp_servers:\s*(.*?)\s*$", re.MULTILINE)
BARE_PROMISE_GUIDANCE = (
    "bare promise completion is rejected; include 검증 명령/결과, 최종 산출물 경로, 마지막 checkpoint 요약."
)
DIRECT_EXECUTION_GUIDANCE = (
    "Use writing-plans or provide a reviewed: true .agentos/project/exec-plans/active/*.md path. "
    "Alternative: provide one strict [EXECUTION_CONTRACT] block with Goal:/Scope:/Actions:/Verification:/Done When:. "
    "Do not use prd.json/progress.txt or dangerous direct execution shortcuts."
)
MAX_RESULT_SUMMARY = 200
MAX_ESCALATION_SUMMARY = 240
EVENTS_MAX_BYTES = 256 * 1024
EVENTS_MAX_ARCHIVES = 5
OUTCOME_COMPLETED = "completed"
OUTCOME_BLOCKED = "blocked"
OUTCOME_RETRYING = "retrying"
OUTCOME_STOPPED = "stopped"
OUTCOME_RUNNING = "running"
FAILURE_NONE = "none"
FAILURE_COMPLETION_CONTRACT = "completion_contract"
FAILURE_ESCALATION_PENDING = "escalation_pending"
FAILURE_TIMEOUT = "timeout"
FAILURE_STAGNATION = "stagnation"
FAILURE_CLI_ERROR = "cli_error"
FAILURE_LAUNCH = "launch"
FAILURE_DISPATCH = "dispatch"
FAILURE_OUTPUT_LAST_MESSAGE = "output_last_message"
FAILURE_ITERATION_BUDGET = "iteration_budget"
FAILURE_CD_LIMIT = "cd_limit"
FAILURE_MCP_SELECTION = "mcp_selection"
FAILURE_PLANNING_REQUIRED = "planning_required"
FAILURE_REVIEW_REQUIRED = "review_required"
FAILURE_INTERRUPTED = "interrupted"


def diagnostic_for_event(event_type: str, stop_reason: str = "") -> tuple[str, str, str]:
    if event_type == "loop_completed":
        return OUTCOME_COMPLETED, FAILURE_NONE, "completion promise accepted with required evidence"
    if event_type in {"escalation_pending", "escalation_requested"}:
        return OUTCOME_BLOCKED, FAILURE_ESCALATION_PENDING, "operator response may be required before completion"
    if event_type == "completion_contract_missing":
        return OUTCOME_RETRYING, FAILURE_COMPLETION_CONTRACT, "completion evidence missing; next iteration should repair closeout"
    if event_type == "timeout":
        return OUTCOME_RETRYING, FAILURE_TIMEOUT, "child timeout surfaced; loop retry behavior unchanged"
    if event_type == "stagnation":
        return OUTCOME_RETRYING, FAILURE_STAGNATION, "child progress stagnation surfaced; loop retry behavior unchanged"
    if event_type == "launch_failure":
        return OUTCOME_RETRYING, FAILURE_LAUNCH, "child launch failure surfaced; loop retry behavior unchanged"
    if event_type == "dispatch_failure":
        return OUTCOME_RETRYING, FAILURE_DISPATCH, "child dispatch failure surfaced; loop retry behavior unchanged"
    if event_type == "output_last_message_fallback":
        return OUTCOME_RETRYING, FAILURE_OUTPUT_LAST_MESSAGE, "last-message fallback used; inspect events.jsonl"
    if event_type == "cli_error":
        return OUTCOME_RETRYING, FAILURE_CLI_ERROR, "child CLI non-zero exit surfaced; loop retry behavior unchanged"
    if event_type == "mcp_selection_error":
        return OUTCOME_STOPPED, FAILURE_MCP_SELECTION, "MCP selection failed before child dispatch"
    if event_type == "planning_redirect":
        return OUTCOME_STOPPED, FAILURE_PLANNING_REQUIRED, "reviewed active plan or strict execution contract required"
    if event_type == "plan_normalized":
        return OUTCOME_STOPPED, FAILURE_REVIEW_REQUIRED, "normalized plan requires review before execution"
    if event_type == "progress_heartbeat":
        return OUTCOME_RUNNING, FAILURE_NONE, "child still running; no terminal outcome yet"
    if event_type == "loop_stopped":
        if stop_reason.startswith("max_iterations:"):
            return OUTCOME_STOPPED, FAILURE_ITERATION_BUDGET, "iteration budget exhausted"
        if stop_reason.startswith("cd_limit:"):
            return OUTCOME_STOPPED, FAILURE_CD_LIMIT, "CD limit reached"
        if stop_reason.startswith("interrupted") or stop_reason.startswith("signal:"):
            return OUTCOME_STOPPED, FAILURE_INTERRUPTED, "parent interrupt cleanup attempted"
        return OUTCOME_STOPPED, FAILURE_CLI_ERROR, "loop stopped before completion"
    return OUTCOME_RUNNING, FAILURE_NONE, "diagnostic pending"


class _LoopSignalStop(Exception):
    def __init__(self, signum: int):
        self.signum = signum
        super().__init__(signum)


def detect_promise(output: str, promise: str) -> bool:
    for match in PROMISE_RE.finditer(output):
        line_start = output.rfind("\n", 0, match.start()) + 1
        line_end = output.find("\n", match.end())
        if line_end == -1:
            line_end = len(output)
        if "[PROMPT_ECHO]" in output[line_start:line_end]:
            continue
        if match.group(1).strip() == promise:
            return True
    return False


def has_completion_evidence(output: str) -> bool:
    evidence_groups = [
        ("검증 명령/결과:", "검증 결과:", "verification_command=", "verification_result=", "verification="),
        ("최종 산출물 경로:", "최종 산출물:", "final_artifact=", "artifact=", "final_conclusion_path:"),
        ("마지막 checkpoint 요약:", "마지막 checkpoint:", "last_checkpoint="),
    ]
    return all(any(token in output for token in group) for group in evidence_groups)


def is_harness_evolution_context(prompt: str, plan_path: str) -> bool:
    haystack = f"{prompt}\n{plan_path}".lower()
    return any(
        token in haystack
        for token in (
            "harness-evolution",
            "harness evolution",
            "harness-ralph-loop-evolution-strategy",
        )
    )


def has_evolution_completion_evidence(output: str) -> bool:
    required_tokens = [
        "strategy_artifact_path:",
        "final_conclusion_path:",
        "harness-architect: PASS",
    ]
    return all(token in output for token in required_tokens)


def detect_escalation(output: str) -> bool:
    return bool(ESCALATION_RE.search(output))


def summarize_result(output: str, limit: int = MAX_RESULT_SUMMARY) -> str:
    single_line = " ".join(output.split())
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 3] + "..."


def summarize_escalation(text: str, limit: int = MAX_ESCALATION_SUMMARY) -> str:
    match = ESCALATION_RE.search(text)
    summary = (match.group(1) if match else text).strip()
    if not summary:
        return "escalation_detected"
    return summarize_result(summary, limit=limit)


def extract_plan_path(prompt: str) -> str:
    match = PLAN_PATH_RE.search(prompt)
    if not match:
        return ""
    return match.group(1)


def parse_execution_contract(prompt: str) -> Optional[dict[str, str]]:
    matches = list(EXECUTION_CONTRACT_RE.finditer(prompt))
    if len(matches) != 1:
        return None

    body = matches[0].group("body").strip()
    values: dict[str, list[str]] = {field: [] for field in EXECUTION_CONTRACT_FIELDS}
    current_field = ""
    seen_fields: list[str] = []
    field_re = re.compile(r"^(Goal|Scope|Actions|Verification|Done When):\s*(.*)$")

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        field_match = field_re.match(line)
        if field_match:
            field_name = field_match.group(1)
            current_field = field_name
            seen_fields.append(field_name)
            values[field_name].append(field_match.group(2).strip())
            continue
        if not current_field:
            return None
        values[current_field].append(line.strip())

    if seen_fields != EXECUTION_CONTRACT_FIELDS:
        return None

    normalized = {
        field: "\n".join(part for part in values[field] if part).strip()
        for field in EXECUTION_CONTRACT_FIELDS
    }
    if any(not normalized[field] for field in EXECUTION_CONTRACT_FIELDS):
        return None
    return normalized


def parse_plan_mcp_servers(raw_value: str) -> list[str]:
    value = raw_value.strip()
    if value in {"", "[]"}:
        return []

    parsed: object
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        if not (value.startswith("[") and value.endswith("]")):
            raise ValueError("mcp_servers must be a list, for example [] or [penpot]")
        inner = value[1:-1].strip()
        parsed = [] if not inner else [
            part.strip().strip("'\"")
            for part in inner.split(",")
        ]

    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise ValueError("mcp_servers must be a list of server names")

    names = [item.strip() for item in parsed]
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError(f"invalid MCP server name: {name}")
    if "none" in names and len(names) != 1:
        raise ValueError("mcp_servers cannot combine none with server names")
    if names == ["none"]:
        return []
    return names


def extract_plan_mcp_servers(plan_text: str) -> list[str]:
    match = MCP_SERVERS_RE.search(plan_text)
    if not match:
        return []
    return parse_plan_mcp_servers(match.group(1))


def format_mcp_servers(servers: list[str]) -> str:
    return json.dumps(servers, ensure_ascii=True, separators=(",", ":"))


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].strip("-") or "execution-contract"


def build_loop_id(started_at: str, prompt: str) -> str:
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:10]
    compact_ts = started_at.replace("-", "").replace(":", "").replace("T", "-").replace("Z", "")
    return f"loop-{compact_ts}-{digest}"


def build_escalation_id(iteration: int) -> str:
    return f"esc-{iteration:03d}"


def load_default_cli(project_root: Path) -> Optional[str]:
    config_file = project_root / LOOP_CONFIG_FILE
    if not config_file.exists():
        return None

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    default_cli = data.get("default_cli")
    if default_cli in {"claude", "codex", "gemini"}:
        return default_cli
    return None


def confirm_cli_execution(cli: str, input_fn=input) -> bool:
    prompt = f"랄프 루프를 '{cli}' agent로 실행합니다. 계속할까요? [y/N]: "
    try:
        answer = input_fn(prompt).strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


class HarnessLoop:
    def __init__(
        self,
        state_file: Path,
        history_file: Path,
        cd_limit: int = 30,
        hist_limit: int = 500,
        cli_timeout: int = 300,
        stagnation_timeout: float = 60.0,
    ):
        self.state_file = state_file
        self.history_file = history_file
        self.events_file = state_file.parent / "events.jsonl"
        self.cd_limit = cd_limit
        self.hist_limit = hist_limit
        self.cli_timeout = cli_timeout
        self.stagnation_timeout = stagnation_timeout
        self.child_progress_poll_seconds = CHILD_PROGRESS_POLL_SECONDS
        self.child_progress_heartbeat_seconds = CHILD_PROGRESS_HEARTBEAT_SECONDS
        self.events_max_bytes = EVENTS_MAX_BYTES
        self.events_max_archives = EVENTS_MAX_ARCHIVES
        self._recent_outputs: list[int] = []  # oscillation 감지용
        self.project_root = state_file.parents[3]
        self._active_adapter: Optional[CLIAdapter] = None

    def _ensure_trace_dir(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _events_archives(self) -> list[Path]:
        return sorted(self.events_file.parent.glob("events.*.jsonl.gz"))

    def _rotate_events_if_needed(self, next_event_size: int) -> None:
        if self.events_max_bytes <= 0:
            return
        if not self.events_file.exists():
            return
        active_size = self.events_file.stat().st_size
        if active_size == 0 or active_size + next_event_size <= self.events_max_bytes:
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = self.events_file.with_name(f"events.{timestamp}.jsonl.gz")
        suffix = 2
        while archive.exists():
            archive = self.events_file.with_name(f"events.{timestamp}-{suffix}.jsonl.gz")
            suffix += 1

        with self.events_file.open("rb") as src, gzip.open(archive, "wb") as dst:
            dst.write(src.read())
        self.events_file.write_text("", encoding="utf-8")

        if self.events_max_archives >= 0:
            archives = self._events_archives()
            while len(archives) > self.events_max_archives:
                oldest = archives.pop(0)
                oldest.unlink(missing_ok=True)

    def _append_event(self, event_type: str, iteration: int, summary: str, **extra: str) -> None:
        self._ensure_trace_dir()
        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": event_type,
            "iteration": iteration,
            "summary": summary,
        }
        for key, value in extra.items():
            if value not in (None, ""):
                event[key] = value
        line = json.dumps(event, ensure_ascii=True) + "\n"
        self._rotate_events_if_needed(len(line.encode("utf-8")))
        with self.events_file.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def _set_diagnostics(
        self,
        state: LoopState,
        event_type: str,
        *,
        stop_reason: Optional[str] = None,
        status_hint: Optional[str] = None,
    ) -> None:
        outcome_code, failure_class, default_hint = diagnostic_for_event(
            event_type,
            state.stop_reason if stop_reason is None else stop_reason,
        )
        state.outcome_code = outcome_code
        state.failure_class = failure_class
        state.status_hint = status_hint or default_hint

    def _append_diagnostic_event(self, event_type: str, state: LoopState, summary: str, **extra: str) -> None:
        self._append_event(
            event_type,
            state.iteration,
            summary,
            outcome_code=state.outcome_code,
            failure_class=state.failure_class,
            status_hint=state.status_hint,
            **extra,
        )

    def _read_history_lines(self) -> list[str]:
        if not self.history_file.exists():
            return []
        return self.history_file.read_text(encoding="utf-8").splitlines()

    def _read_history_delta(self, offset: int) -> tuple[list[str], int]:
        if not self.history_file.exists():
            return [], 0

        size = self.history_file.stat().st_size
        if offset > size:
            offset = 0
        if offset == size:
            return [], size

        with self.history_file.open("rb") as fh:
            fh.seek(offset)
            data = fh.read()
        return data.decode("utf-8", errors="replace").splitlines(), size

    def _summarize_prompt(self, prompt: str, limit: int = 120) -> str:
        single_line = " ".join(prompt.split())
        if len(single_line) <= limit:
            return single_line
        return single_line[: limit - 3] + "..."

    def _extract_ts(self, line: str) -> str:
        match = re.match(r"^\[([^\]]+)\]", line)
        if not match:
            return "null"
        return f'"{match.group(1)}"'

    def _apply_history_events(self, state: LoopState, new_lines: list[str]) -> None:
        for line in new_lines:
            if "[CHECKPOINT]" in line:
                parts = line.split(" | ")
                headline = parts[0].split("[CHECKPOINT] ", 1)[-1].strip()
                summary = parts[1].strip() if len(parts) > 1 else headline
                state.last_checkpoint_at = self._extract_ts(line)
                state.last_event = "checkpoint"
                state.current_phase = headline
                state.current_task = summary
                state.current_step = headline
                if not state.result_summary:
                    state.result_summary = summary
                self._append_event(
                    "checkpoint_detected",
                    state.iteration,
                    headline,
                    loop_id=state.loop_id,
                    plan_path=state.plan_path,
                    phase=headline,
                    task=summary,
                )
            elif "[LOOP_STOP" in line:
                summary = line.split("] ", 1)[-1].strip()
                state.last_event = "loop_stopped"
                state.stop_reason = summary
                self._set_diagnostics(state, "loop_stopped")
                self._append_diagnostic_event("loop_stopped", state, summary, loop_id=state.loop_id)
            else:
                escalation_match = ESCALATION_RE.search(line)
                if not escalation_match:
                    continue
                summary = summarize_escalation(escalation_match.group(0))
                if not state.pending_escalation_id:
                    state.pending_escalation_id = build_escalation_id(state.iteration)
                state.pending_escalation_summary = summary or state.pending_escalation_summary
                state.last_event = "escalation_pending"
                state.current_task = "Continuing default plan"
                state.current_step = "Awaiting optional escalation response"
                self._set_diagnostics(state, "escalation_pending")
                self._append_diagnostic_event(
                    "escalation_requested",
                    state,
                    state.pending_escalation_summary or "escalation_detected",
                    loop_id=state.loop_id,
                    request_id=state.pending_escalation_id,
                )

    def _emit_progress_heartbeat(self, state: LoopState) -> None:
        if state.last_checkpoint_at != "null":
            summary = f"child running; last_checkpoint_at={state.last_checkpoint_at}"
            step = "Heartbeat: waiting for next child checkpoint"
        else:
            summary = "child running; awaiting first child checkpoint"
            step = "Heartbeat: awaiting first child checkpoint"
        state.last_event = "progress_heartbeat"
        state.current_phase = f"Iteration {state.iteration}"
        state.current_task = "Running child CLI"
        state.current_step = step
        state.result_summary = summary
        self._set_diagnostics(state, "progress_heartbeat")
        state.to_file(self.state_file)
        self._append_diagnostic_event(
            "progress_heartbeat",
            state,
            summary,
            loop_id=state.loop_id,
            plan_path=state.plan_path,
            last_checkpoint_at=state.last_checkpoint_at,
        )

    def _run_child_with_progress(
        self,
        adapter: CLIAdapter,
        prompt: str,
        state: LoopState,
        history_before: list[str],
    ) -> tuple[int, str]:
        result: dict[str, object] = {}

        def target() -> None:
            try:
                result["value"] = adapter.run(prompt, timeout=self.cli_timeout)
            except BaseException as exc:  # pragma: no cover - propagated immediately after join
                result["error"] = exc

        history_offset = self.history_file.stat().st_size if self.history_file.exists() else 0
        worker = threading.Thread(target=target, daemon=True)
        self._active_adapter = adapter
        try:
            worker.start()
            last_reflection_at = time.monotonic()

            while worker.is_alive():
                worker.join(timeout=self.child_progress_poll_seconds)
                new_lines, history_offset = self._read_history_delta(history_offset)
                if new_lines:
                    self._apply_history_events(state, new_lines)
                    state.to_file(self.state_file)
                    last_reflection_at = time.monotonic()
                    continue

                if worker.is_alive() and time.monotonic() - last_reflection_at >= self.child_progress_heartbeat_seconds:
                    self._emit_progress_heartbeat(state)
                    last_reflection_at = time.monotonic()

            if "error" in result:
                raise result["error"]  # type: ignore[misc]

            final_new_lines, history_offset = self._read_history_delta(history_offset)
            if final_new_lines:
                self._apply_history_events(state, final_new_lines)
                state.to_file(self.state_file)

            return result["value"]  # type: ignore[return-value]
        finally:
            self._active_adapter = None

    def _is_reviewed_active_plan(self, plan_path: str) -> bool:
        if not ACTIVE_PLAN_PATH_RE.fullmatch(plan_path):
            return False
        path = self.project_root / plan_path
        if not path.exists():
            return False
        return bool(REVIEWED_RE.search(path.read_text(encoding="utf-8")))

    def _build_materialized_plan_path(self, goal: str) -> Path:
        active_dir = self.project_root / ".agentos" / "project" / "exec-plans" / "active"
        active_dir.mkdir(parents=True, exist_ok=True)
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        base_name = f"{date_prefix}-{slugify(goal)}"
        candidate = active_dir / f"{base_name}.md"
        suffix = 2
        while candidate.exists():
            candidate = active_dir / f"{base_name}-{suffix}.md"
            suffix += 1
        return candidate

    def _write_materialized_plan(self, path: Path, contract: dict[str, str]) -> None:
        title = contract["Goal"].strip().rstrip(".")
        plan_text = "\n".join(
            [
                f"# {title} 구현 계획",
                "",
                "> **상태:** 구현 계획 (리뷰 대기)<br>",
                f"> **작성일:** {datetime.now().strftime('%Y-%m-%d')}<br>",
                "> mcp_servers: []",
                "",
                "> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.",
                "",
                f"**목표:** {contract['Goal']}",
                "",
                f"**사용자 결과:** 사용자는 `{contract['Goal']}` 작업이 바로 실행되지 않고, 리뷰 가능한 active plan으로 먼저 저장된 것을 확인한다.",
                "",
                "**진행 상태:** 실행 계약을 active plan으로 정규화했고, Gate 2 리뷰 전까지 구현은 차단된 상태다.",
                "",
                "**아키텍처:** strict [EXECUTION_CONTRACT] 입력을 canonical active plan으로 정규화했다. long prompt transport는 별도 클래스 없이 active plan으로 물질화하고 Rule 6 리뷰 후에만 실행한다.",
                "",
                "**기술 스택:** Markdown, Python 3, Bash, existing harness loop engine",
                "",
                "## 진행 스냅샷",
                "",
                "| 필드 | 현재 값 |",
                "|---|---|",
                "| 전체 상태 | 리뷰 대기 |",
                "| 완료됨 | strict execution contract를 active plan 문서로 저장했다. |",
                "| 현재 위치 | plan-reviewer와 principle-auditor 리뷰가 필요하다. |",
                "| 다음 단계 | 리뷰어가 계획의 실행 가능성과 보호 경로 경계를 검토한다. |",
                "| 완료 신호 | `reviewed: true`가 기록되고 필요한 reviewer PASS evidence가 HISTORY 또는 계획 본문에 남는다. |",
                "",
                "## 사용자 결과 요약",
                "",
                "| 질문 | 답변 |",
                "|---|---|",
                f"| 사용자가 무엇을 얻게 되는가? | `{contract['Goal']}` 작업을 위한 리뷰 대기 active plan. |",
                "| 누구를 위한 것인가? | harness loop를 통해 긴 실행 계약을 제출한 사용자와 리뷰어. |",
                "| 일상 사용에서 무엇이 달라지는가? | 직접 실행 대신 리뷰 가능한 계획 문서가 먼저 생긴다. |",
                "| 무엇은 바뀌지 않는가? | 리뷰 전 구현 차단, protected path 승인, prompt boundary 규칙은 그대로 유지된다. |",
                "",
                "## 사용자 진행 계획",
                "",
                "| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |",
                "|---|---|---|---|",
                "| 1. 계약 정규화 | active plan 문서가 생성된다. | `.agentos/project/exec-plans/active/` | `plan_lifecycle.py refresh` 완료 |",
                "| 2. 리뷰 대기 | 실행 전 reviewer gate가 명확히 보인다. | 계획 본문, HISTORY evidence | reviewer PASS 기록 |",
                "",
                "## MCP 사용 계획",
                "",
                "- Required MCPs: none",
                "- Purpose: none. This normalized plan starts MCP-free.",
                "- When Used: never until a reviewer explicitly updates `mcp_servers`.",
                "- Preflight: no MCP endpoint or token check required.",
                "- Expected Evidence: child launch renders `mcp_servers={}`.",
                "",
                "## 의존성 분석",
                "",
                "- 외부 의존성: 없음",
                "- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.",
                "",
                "---",
                "",
                "## 정규화된 실행 계약",
                "",
                "```text",
                "[EXECUTION_CONTRACT]",
                f"Goal: {contract['Goal']}",
                f"Scope: {contract['Scope']}",
                f"Actions: {contract['Actions']}",
                f"Verification: {contract['Verification']}",
                f"Done When: {contract['Done When']}",
                "[/EXECUTION_CONTRACT]",
                "```",
                "",
                "## 리뷰 게이트",
                "",
                "- plan-reviewer PASS 필요",
                "- principle-auditor CLEAN 필요",
                "- reviewed: true 없이는 direct execution 불가",
                "",
            ]
        )
        path.write_text(plan_text, encoding="utf-8")

    def _refresh_plan_lifecycle(self) -> None:
        script = Path(__file__).resolve().parents[1] / "writing-plans" / "scripts" / "plan_lifecycle.py"
        subprocess.run(
            ["python3", str(script), "refresh", "--root", str(self.project_root)],
            check=True,
            capture_output=True,
            text=True,
        )

    def _stop_for_plan_normalization(self, state: LoopState, contract: dict[str, str]) -> int:
        materialized_path = self._build_materialized_plan_path(contract["Goal"])
        self._write_materialized_plan(materialized_path, contract)
        self._refresh_plan_lifecycle()
        state.active = False
        state.plan_path = materialized_path.relative_to(self.project_root).as_posix()
        state.last_event = "plan_normalized"
        state.stop_reason = "review_required"
        state.current_phase = "Normalization Gate"
        state.current_task = "Execution Contract normalized"
        state.current_step = "Awaiting plan-reviewer and principle-auditor"
        state.result_summary = summarize_result(f"plan_normalized {state.plan_path}")
        self._set_diagnostics(state, "plan_normalized")
        state.to_file(self.state_file)
        self._append_diagnostic_event(
            "plan_normalized",
            state,
            f"active plan으로 물질화: {state.plan_path}",
            loop_id=state.loop_id,
            plan_path=state.plan_path,
        )
        print(f"[plan_normalized] active: false stop_reason=review_required")
        print(f"Generated active plan: {state.plan_path}")
        print("Next gate: plan-reviewer PASS + principle-auditor CLEAN")
        print("Direct execution stays blocked until reviewed: true is present; do not bypass with prd.json/progress.txt or dangerous direct execution.")
        return 0

    def _stop_for_planning_redirect(self, state: LoopState) -> int:
        state.active = False
        state.last_event = "planning_redirect"
        state.stop_reason = "planning_required"
        state.current_phase = "Planning Gate"
        state.current_task = "writing-plans required"
        state.current_step = "Provide reviewed: true active plan path or strict EXECUTION_CONTRACT; prd.json/progress.txt and dangerous direct execution are rejected"
        state.result_summary = summarize_result("planning_redirect -> writing-plans -> no prd.json/progress.txt shortcuts")
        self._set_diagnostics(state, "planning_redirect")
        state.to_file(self.state_file)
        self._append_diagnostic_event(
            "planning_redirect",
            state,
            "direct execution blocked; writing-plans required",
            loop_id=state.loop_id,
            plan_path=state.plan_path,
        )
        print("[planning_redirect] active: false stop_reason=planning_required")
        print(DIRECT_EXECUTION_GUIDANCE)
        return 1

    def _apply_execution_gate(self, state: LoopState) -> Tuple[bool, Optional[int]]:
        reviewed_plan_path = ""
        active_match = ACTIVE_PLAN_PATH_RE.search(state.prompt)
        if active_match:
            candidate = active_match.group(1)
            if self._is_reviewed_active_plan(candidate):
                reviewed_plan_path = candidate
        if reviewed_plan_path:
            state.plan_path = reviewed_plan_path
            return True, None

        contract = parse_execution_contract(state.prompt)
        if contract:
            return False, self._stop_for_plan_normalization(state, contract)

        return False, self._stop_for_planning_redirect(state)

    def _read_plan_mcp_servers(self, plan_path: str) -> tuple[list[str], str]:
        if not plan_path:
            return [], ""
        path = self.project_root / plan_path
        try:
            plan_text = path.read_text(encoding="utf-8")
            return extract_plan_mcp_servers(plan_text), ""
        except (OSError, ValueError) as exc:
            return [], str(exc)

    def _render_mcp_config_args(self, servers: list[str]) -> tuple[list[str], str]:
        helper = self.project_root / ".agents" / "mcp" / "scripts" / "render-codex-mcp-config.py"
        if not helper.exists():
            if not servers:
                return ["-c", "mcp_servers={}"], ""
            return [], f"missing MCP render helper: {helper}"

        cmd = ["python3", str(helper), "--print-argv"]
        if servers:
            for server in servers:
                cmd.extend(["--server", server])
        else:
            cmd.extend(["--server", "none"])

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            return [], detail or f"MCP render helper failed: exit {result.returncode}"
        rendered = [line for line in result.stdout.splitlines() if line]
        if not rendered:
            return [], "MCP render helper returned no argv tokens"
        return rendered, ""

    def _stop_for_mcp_selection_error(self, state: LoopState, summary: str) -> int:
        state.active = False
        state.last_event = "mcp_selection_error"
        state.stop_reason = "mcp_selection_error"
        state.current_phase = "MCP Selection Gate"
        state.current_task = "Invalid MCP selection"
        state.current_step = summary
        state.result_summary = summarize_result(summary)
        self._set_diagnostics(state, "mcp_selection_error")
        state.deactivate(self.state_file)
        self._append_diagnostic_event(
            "mcp_selection_error",
            state,
            summary,
            loop_id=state.loop_id,
            plan_path=state.plan_path,
            result_summary=state.result_summary,
        )
        print(f"[mcp_selection_error] {summary}")
        return 1

    def _cd_score(self) -> int:
        if not self.history_file.exists():
            return 0
        return self.history_file.read_text().count("[ESCALATION]")

    def _hist_lines(self) -> int:
        if not self.history_file.exists():
            return 0
        return self.history_file.read_text().count("\n")

    def _detect_oscillation(self, output: str) -> bool:
        """AGENTS.md §3.2: oscillation_cycle 기반 주기-2 사이클 감지"""
        self._recent_outputs.append(hash(output))
        if len(self._recent_outputs) >= 4:
            # 최근 4개에서 A,B,A,B 패턴 확인
            r = self._recent_outputs[-4:]
            if r[0] == r[2] and r[1] == r[3] and r[0] != r[1]:
                return True
        return False

    def _iteration_budget_exceeded(self, state: LoopState) -> bool:
        if state.max_iterations <= 0:
            return False
        return state.iteration > state.max_iterations

    def _mark_escalation_pending(self, state: LoopState, summary: str) -> None:
        if not state.pending_escalation_id:
            state.pending_escalation_id = build_escalation_id(state.iteration)
        if summary:
            state.pending_escalation_summary = summary
        elif not state.pending_escalation_summary:
            state.pending_escalation_summary = "escalation_detected"
        state.last_event = "escalation_pending"
        state.current_task = "Continuing default plan"
        state.current_step = "Awaiting optional escalation response"
        state.blocked_reason = ""
        state.stop_reason = ""
        self._set_diagnostics(state, "escalation_pending")
        state.to_file(self.state_file)
        self._append_diagnostic_event(
            "escalation_requested",
            state,
            state.pending_escalation_summary,
            loop_id=state.loop_id,
            request_id=state.pending_escalation_id,
            plan_path=state.plan_path,
        )

    def _peek_pending_override(self, state: LoopState) -> tuple[str, str, str]:
        override = state.pending_override_response.strip()
        if not override:
            return "", "", ""
        if not state.pending_escalation_id:
            state.pending_override_response = ""
            state.to_file(self.state_file)
            self._append_event(
                "escalation_override_ignored",
                state.iteration,
                "stale override without pending escalation",
                loop_id=state.loop_id,
            )
            return "", "", ""

        return override, state.pending_escalation_id, state.pending_escalation_summary or "override applied"

    def _finalize_pending_override(self, state: LoopState, request_id: str, summary: str) -> None:
        state.pending_override_response = ""
        state.pending_escalation_id = ""
        state.pending_escalation_summary = ""
        state.last_event = "escalation_resolved"
        state.current_task = "Continuing default plan"
        state.current_step = "Override applied"
        state.to_file(self.state_file)
        self._append_event(
            "escalation_resolved",
            state.iteration,
            summary,
            loop_id=state.loop_id,
            request_id=request_id,
        )

    def _clear_pending_escalation(self, state: LoopState) -> None:
        state.pending_override_response = ""
        state.pending_escalation_id = ""
        state.pending_escalation_summary = ""

    def _build_prompt(self, state: LoopState, escalation_response: str = "") -> str:
        parts = [
            '먼저 AGENTS.md와 HISTORY.md 최근 10개 항목을 읽어라 (Phase A 프로토콜).\n작업 완료 단계마다 HISTORY.md에 [CHECKPOINT] 또는 [HEARTBEAT]를 기록하라 (Phase B/C 프로토콜).',
            "completion contract: 완료 직전에는 검증 명령/결과, 최종 산출물 경로, 마지막 checkpoint 요약을 반드시 남겨라.",
            f"🔄 Harness Loop iteration {state.iteration} | "
            f"완료 시: <promise>{state.completion_promise}</promise> 출력",
            "",
            state.prompt,  # loop-state.md body 반복 (sh와 동일)
        ]
        if escalation_response:
            parts += ["", f"[ESCALATION_RESPONSE] {escalation_response}"]
        return "\n".join(parts)

    def _cleanup_active_child(self) -> bool:
        adapter = self._active_adapter
        if adapter is None:
            return False
        cleanup = getattr(adapter, "cleanup_active_child", None)
        if not callable(cleanup):
            return False
        try:
            return bool(cleanup())
        except Exception:
            return False

    def _with_signal_cleanup(self, fn):
        if threading.current_thread() is not threading.main_thread():
            return fn()

        previous_handlers: dict[int, signal.Handlers] = {}

        def handle_signal(signum: int, _frame) -> None:
            self._cleanup_active_child()
            raise _LoopSignalStop(signum)

        try:
            for signum in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, handle_signal)
            return fn()
        finally:
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)

    def _stop_for_parent_interrupt(self, state: LoopState, stop_reason: str, summary: str) -> None:
        self._cleanup_active_child()
        state.last_event = "loop_stopped"
        state.stop_reason = stop_reason
        state.current_task = "Stopped"
        state.current_step = summary
        state.result_summary = summarize_result(summary)
        self._clear_pending_escalation(state)
        self._set_diagnostics(state, "loop_stopped", stop_reason=stop_reason)
        state.deactivate(self.state_file)
        self._append_diagnostic_event(
            "loop_stopped",
            state,
            summary,
            loop_id=state.loop_id,
            plan_path=state.plan_path,
            result_summary=state.result_summary,
        )

    def run(self) -> int:
        state = LoopState.from_file(self.state_file)
        if not state.loop_id:
            started_at = state.started_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            state.started_at = started_at
            state.loop_id = build_loop_id(started_at, state.prompt)
        if not state.plan_path:
            state.plan_path = extract_plan_path(state.prompt)
        can_execute, stop_code = self._apply_execution_gate(state)
        if not can_execute:
            return 1 if stop_code is None else stop_code

        selected_mcp_servers, mcp_read_error = self._read_plan_mcp_servers(state.plan_path)
        if mcp_read_error:
            return self._stop_for_mcp_selection_error(state, mcp_read_error)
        state.mcp_servers = format_mcp_servers(selected_mcp_servers)
        mcp_config_args, mcp_render_error = self._render_mcp_config_args(selected_mcp_servers)
        if mcp_render_error:
            return self._stop_for_mcp_selection_error(state, mcp_render_error)
        state.to_file(self.state_file)

        # CLI 결정
        if state.cli == "auto":
            detected = CLIAdapter.detect()
            if not detected:
                print("❌ 사용 가능한 CLI를 찾을 수 없습니다.")
                return 1
            adapter = CLIAdapter.get(detected)
            print(f"🔍 자동 감지된 CLI: {detected}")
        else:
            try:
                adapter = CLIAdapter.get(state.cli)
            except ValueError as e:
                print(f"❌ {e}")
                return 1
        adapter.configure_mcp(mcp_config_args)
        adapter.configure_stagnation_timeout(self.stagnation_timeout)

        escalation_response = ""

        print(f"\n{'='*55}")
        print(f"  Harness Loop 시작")
        print(f"  CLI: {state.cli}")
        print(f"  완료 신호: <promise>{state.completion_promise}</promise>")
        print(f"  MCP: {state.mcp_servers}")
        print(f"  최대 반복: {state.max_iterations or '무제한'}")
        print(f"  상태 파일: {self.state_file}")
        print(f"  (중지하려면 Ctrl+C)")
        print(f"{'='*55}\n")

        state.prompt_summary = self._summarize_prompt(state.prompt)
        state.last_event = "loop_started"
        state.current_phase = "Phase A"
        state.current_task = "Loop initialized"
        state.current_step = "Iteration bootstrap"
        self._set_diagnostics(state, "loop_started")
        state.to_file(self.state_file)
        self._append_event(
            "loop_started",
            state.iteration,
            f"CLI={state.cli} max_iterations={state.max_iterations or 'infinity'}",
            loop_id=state.loop_id,
            cli=state.cli,
            completion_promise=state.completion_promise,
            plan_path=state.plan_path,
            mcp_servers=state.mcp_servers,
            prompt_summary=state.prompt_summary,
        )

        def loop_body() -> int:
            while True:
                cd = self._cd_score()
                hist = self._hist_lines()

                print(f"\n{'─'*55}")
                print(f"🔄 Iteration {state.iteration} / {state.max_iterations or '∞'}")
                print(f"📊 CD: {cd}/{self.cd_limit}  HISTORY: {hist}/{self.hist_limit}")
                if self.history_file.exists():
                    lines = self.history_file.read_text().splitlines()
                    if lines:
                        print(f"📋 마지막 로그: {lines[-1]}")
                print(f"{'─'*55}")

                # HEARTBEAT (AGENTS.md §3.2: heartbeat_interval=5)
                if state.iteration % HEARTBEAT_INTERVAL == 0:
                    print(f"💓 [HEARTBEAT] iteration={state.iteration}")

                # 가드레일
                if cd >= self.cd_limit:
                    print(f"🛑 CD 한계({self.cd_limit}) 도달. 루프 중지.")
                    if not state.last_event:
                        state.last_event = "loop_stopped"
                    state.stop_reason = f"cd_limit:{self.cd_limit}"
                    self._clear_pending_escalation(state)
                    self._set_diagnostics(state, "loop_stopped")
                    state.deactivate(self.state_file)
                    self._append_diagnostic_event(
                        "loop_stopped",
                        state,
                        f"CD limit reached: {self.cd_limit}",
                        loop_id=state.loop_id,
                    )
                    return 1

                if hist >= self.hist_limit:
                    print(f"⚡ [TRIGGER 4] HISTORY 압축 기준 도달 ({hist} >= {self.hist_limit})")
                    print(
                        "   run: python3 .agents/skills/harness/core-engine/scripts/compact_history.py "
                        "--history-path HISTORY.md "
                        "--archive-path docs/project/reference/history/2026-04-history-archive.md "
                        "--keep-recent-lines 200"
                    )
                    print("   expected: PASS compact-history ... and HISTORY.md keeps only the recent operational window.")

                if self._iteration_budget_exceeded(state):
                    print(f"🛑 최대 반복({state.max_iterations}) 도달. 루프 중지.")
                    if state.last_event not in {
                        "launch_failure",
                        "dispatch_failure",
                        "output_last_message_fallback",
                        "stagnation",
                        "timeout",
                        "completion_contract_missing",
                        "cli_error",
                    }:
                        state.last_event = "loop_stopped"
                    state.stop_reason = f"max_iterations:{state.max_iterations}"
                    self._clear_pending_escalation(state)
                    self._set_diagnostics(state, "loop_stopped")
                    state.deactivate(self.state_file)
                    self._append_diagnostic_event(
                        "loop_stopped",
                        state,
                        f"Max iterations reached: {state.max_iterations}",
                        loop_id=state.loop_id,
                    )
                    return 1

                # pending override는 iteration 시작 직전에 1회만 소비한다.
                escalation_response, override_request_id, override_summary = self._peek_pending_override(state)
                applied_override = bool(escalation_response)

                # CLI 실행
                prompt = self._build_prompt(state, escalation_response)
                history_before = self._read_history_lines()

                if not applied_override:
                    state.last_event = "iteration_started"
                state.current_phase = f"Iteration {state.iteration}"
                state.current_task = "Running child CLI"
                state.current_step = "Dispatch prompt with override" if applied_override else "Dispatch prompt"
                state.to_file(self.state_file)
                self._append_event(
                    "iteration_started",
                    state.iteration,
                    "Child CLI dispatch with override" if applied_override else "Child CLI dispatch",
                    loop_id=state.loop_id,
                    plan_path=state.plan_path,
                    mcp_servers=state.mcp_servers,
                )
                escalation_response = ""

                print(f"\n[실행 중...]\n")
                try:
                    exit_code, output = self._run_child_with_progress(
                        adapter,
                        prompt,
                        state,
                        history_before,
                    )
                except FileNotFoundError:
                    print(f"❌ CLI가 설치되지 않았습니다: {state.cli}")
                    state.last_event = "loop_stopped"
                    state.stop_reason = f"cli_not_found:{state.cli}"
                    state.current_task = "Stopped"
                    state.current_step = "CLI not found"
                    self._set_diagnostics(state, "loop_stopped")
                    state.deactivate(self.state_file)
                    self._append_diagnostic_event(
                        "loop_stopped",
                        state,
                        f"CLI not found: {state.cli}",
                        loop_id=state.loop_id,
                    )
                    return 1

                print(output)

                if applied_override:
                    self._finalize_pending_override(state, override_request_id, override_summary)

                state.to_file(self.state_file)

                has_promise = detect_promise(output, state.completion_promise)
                requires_evolution_evidence = is_harness_evolution_context(state.prompt, state.plan_path)
                has_base_evidence = has_completion_evidence(output)
                has_all_evidence = has_base_evidence and (
                    has_evolution_completion_evidence(output) if requires_evolution_evidence else True
                )
                if has_promise and exit_code == 0 and has_all_evidence:
                    print(f"\n✅ 완료 신호 감지!")
                    state.active = False
                    state.last_event = "loop_completed"
                    state.stop_reason = "completed"
                    self._clear_pending_escalation(state)
                    state.current_task = "Completed"
                    state.current_step = (
                        "completion-after-quiet promise detected"
                        if "completion-after-quiet" in output
                        else "Promise detected"
                    )
                    state.result_summary = summarize_result(output)
                    self._set_diagnostics(state, "loop_completed")
                    state.to_file(self.state_file)
                    self._append_diagnostic_event(
                        "loop_completed",
                        state,
                        "Completion promise detected",
                        loop_id=state.loop_id,
                        plan_path=state.plan_path,
                        result_summary=state.result_summary,
                    )
                    print(f"🎉 Harness Loop 정상 완료 (총 {state.iteration}회)")
                    return 0
                if has_promise and exit_code == 0 and not has_all_evidence:
                    if requires_evolution_evidence and has_base_evidence:
                        print("⚠️  completion contract 누락. 하네스 진화 작업은 strategy_artifact_path, final_conclusion_path, harness-architect: PASS가 추가로 필요합니다.")
                        state.current_step = "검증 명령/결과 + 최종 산출물 경로 + 마지막 checkpoint 요약 + strategy_artifact_path + final_conclusion_path + harness-architect: PASS 필요"
                    else:
                        print(f"⚠️  completion contract 누락. {BARE_PROMISE_GUIDANCE}")
                        state.current_step = "bare promise rejected; 검증 명령/결과 + 최종 산출물 경로 + 마지막 checkpoint 요약 필요"
                    state.last_event = "completion_contract_missing"
                    state.current_task = "Completion contract missing"
                    state.result_summary = summarize_result(output)
                    self._set_diagnostics(state, "completion_contract_missing")
                    state.to_file(self.state_file)
                    self._append_diagnostic_event(
                        "completion_contract_missing",
                        state,
                        "completion contract missing",
                        loop_id=state.loop_id,
                        plan_path=state.plan_path,
                        result_summary=state.result_summary,
                    )

                if exit_code == -2:
                    print(f"⚠️  [STAGNATION] Codex child progress 정체 감지. 다음 iteration으로 진행합니다.")
                    state.last_event = "stagnation"
                    state.current_task = "Child CLI stagnation"
                    state.current_step = "Stagnation handled"
                    state.result_summary = summarize_result(output)
                    self._set_diagnostics(state, "stagnation")
                    state.to_file(self.state_file)
                    self._append_diagnostic_event(
                        "stagnation",
                        state,
                        "Child CLI stagnation detected",
                        loop_id=state.loop_id,
                        plan_path=state.plan_path,
                        result_summary=state.result_summary,
                    )
                elif exit_code == -1:
                    print(f"⚠️  [TIMEOUT] CLI 응답 시간 초과. 루프 계속...")
                    state.last_event = "timeout"
                    state.current_task = "Child CLI timeout"
                    state.current_step = "Timeout handled"
                    self._clear_pending_escalation(state)
                    self._set_diagnostics(state, "timeout")
                    state.to_file(self.state_file)
                    self._append_diagnostic_event("timeout", state, "CLI timeout", loop_id=state.loop_id)
                elif exit_code != 0:
                    print(f"⚠️  CLI 오류 (exit {exit_code}). 루프 계속...")
                    failure_summary = "CLI exit"
                    if "launch failure" in output:
                        state.last_event = "launch_failure"
                        state.current_task = "Child CLI launch failure"
                        state.current_step = "launch failure"
                        failure_summary = "launch failure"
                    elif "dispatch failure" in output:
                        state.last_event = "dispatch_failure"
                        state.current_task = "Child CLI dispatch failure"
                        state.current_step = "dispatch failure"
                        failure_summary = "dispatch failure"
                    elif "output_last_message" in output:
                        state.last_event = "output_last_message_fallback"
                        state.current_task = "Child CLI output_last_message fallback"
                        state.current_step = "output_last_message fallback"
                        failure_summary = "output_last_message fallback"
                    else:
                        state.last_event = "cli_error"
                        state.current_task = "Child CLI error"
                        state.current_step = f"Exit {exit_code}"
                    self._clear_pending_escalation(state)
                    self._set_diagnostics(state, state.last_event)
                    state.to_file(self.state_file)
                    self._append_diagnostic_event(
                        state.last_event,
                        state,
                        f"{failure_summary} | events.jsonl trace surface preserved",
                        loop_id=state.loop_id,
                        plan_path=state.plan_path,
                        result_summary=summarize_result(output),
                    )

                # Oscillation 감지 (AGENTS.md §3.2: oscillation_cycle)
                if self._detect_oscillation(output):
                    print(f"🔁 [OSCILLATION] 주기-2 반복 감지. advisory escalation으로 기록하고 기본 진행을 유지합니다.")
                    self._mark_escalation_pending(state, "oscillation_detected")

                # 에스컬레이션 감지
                elif detect_escalation(output):
                    escalation_summary = summarize_escalation(output)
                    self._mark_escalation_pending(state, escalation_summary)

                # 다음 반복
                state.bump_iteration()
                state.to_file(self.state_file)

        try:
            return self._with_signal_cleanup(loop_body)
        except KeyboardInterrupt:
            self._stop_for_parent_interrupt(
                state,
                "interrupted",
                "KeyboardInterrupt received; active child cleanup attempted",
            )
            raise
        except _LoopSignalStop as exc:
            signal_name = signal.Signals(exc.signum).name
            self._stop_for_parent_interrupt(
                state,
                f"signal:{signal_name}",
                f"Received {signal_name}; active child cleanup attempted",
            )
            if exc.signum == signal.SIGINT:
                state.stop_reason = "interrupted"
                state.to_file(self.state_file)
                raise KeyboardInterrupt
            raise SystemExit(128 + exc.signum)


def main():
    parser = argparse.ArgumentParser(
        description="harness_loop.py — Python Harness Loop (harness-loop.sh 대체)"
    )
    parser.add_argument("prompt", nargs="*", help="실행할 프롬프트")
    parser.add_argument("--cli", default="auto",
                        choices=["auto", "claude", "gemini", "codex"])
    parser.add_argument("--yes", action="store_true",
                        help="시작 확인 프롬프트를 생략")
    parser.add_argument("--max-iterations", type=int, default=30)
    parser.add_argument("--completion-promise", default="HARNESS_COMPLETE")
    parser.add_argument("--resume", action="store_true",
                        help="loop-state.md에서 재개")
    parser.add_argument("--dry-run", action="store_true",
                        help="loop-state.md 초기화만 수행, CLI 호출 없음")
    parser.add_argument("--stagnation-timeout", type=float, default=60.0,
                        help="Codex child no-progress timeout in seconds (must be > 0, default: 60)")
    args = parser.parse_args()
    if args.stagnation_timeout <= 0:
        parser.error("--stagnation-timeout must be > 0")

    script_dir = Path(__file__).parent
    try:
        project_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip())
    except subprocess.CalledProcessError:
        project_root = script_dir.parent.parent

    state_file = project_root / ".agents/traces/harness/loop-state.md"
    history_file = project_root / "HISTORY.md"

    if args.resume:
        if not state_file.exists():
            print("❌ 재개할 상태 파일이 없습니다.")
            sys.exit(1)
        resumed_state = LoopState.from_file(state_file)
        if not args.dry_run and not args.yes and not confirm_cli_execution(resumed_state.cli):
            print("🛑 사용자 확인으로 랄프 루프 실행을 중단했습니다.")
            sys.exit(1)
        print(f"🔄 기존 루프 재개: {state_file}")
    else:
        prompt = " ".join(args.prompt)
        if not prompt:
            parser.print_help()
            sys.exit(1)
        resolved_cli = args.cli
        if resolved_cli == "auto":
            configured_cli = load_default_cli(project_root)
            if configured_cli:
                resolved_cli = configured_cli

        if not args.dry_run and not args.yes and not confirm_cli_execution(resolved_cli):
            print("🛑 사용자 확인으로 랄프 루프 실행을 중단했습니다.")
            sys.exit(1)

        state = LoopState(
            cli=resolved_cli,
            max_iterations=args.max_iterations,
            completion_promise=args.completion_promise,
            started_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            prompt=prompt,
        )
        state.loop_id = build_loop_id(state.started_at, prompt)
        state.plan_path = extract_plan_path(prompt)
        state.to_file(state_file)

        if args.dry_run:
            state.active = False
            state.last_event = "loop_stopped"
            state.stop_reason = "dry_run"
            state.current_task = "Dry run"
            state.current_step = "State initialized without CLI dispatch"
            state.to_file(state_file)
            print(f"[DRY-RUN] CLI 호출 없이 loop-state.md만 초기화")
            print(f"프롬프트:\n{prompt}")
            sys.exit(0)

        print(f"🆕 새 루프 시작: {state_file}")

    loop = HarnessLoop(
        state_file=state_file,
        history_file=history_file,
        stagnation_timeout=args.stagnation_timeout,
    )
    sys.exit(loop.run())


if __name__ == "__main__":
    main()
