from __future__ import annotations
from pathlib import Path
from typing import Any

from agentos.observability.plan_parser import parse_exec_plan, status_to_board_status


def emit_plan_status_changed(plan_path: "Path | str") -> dict[str, Any]:
    path = Path(plan_path)
    text = path.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)
    if not summary.title:
        raise ValueError(f"Could not find a title (H1) in {plan_path}")

    board_status = status_to_board_status(summary.status, summary.reviewed)

    return {
        "event": "PLAN_STATUS_CHANGED",
        "plan_path": str(plan_path),
        "title": summary.title,
        "status_text": summary.status,
        "reviewed": summary.reviewed,
        "board_status": board_status,
    }


def emit_plan_writing_started(
    user_request_summary: str,
    agent_name: str,
    session_info: str,
    plan_path: "Path | str | None" = None,
    plan_title: str | None = None,
) -> "dict[str, Any]":
    """
    사용자가 계획 문서 작성을 요청한 즉시 호출한다.
    어댑터 등록/전송은 호출자(writing-plans 스킬)가 담당한다.
    반환값: notifier.notify() 또는 notify_and_wait()에 전달할 payload dict.
    """
    return {
        "event": "PLAN_WRITING_STARTED",
        "user_request": user_request_summary,
        "agent": agent_name,
        "session": session_info,
        "plan_path": str(plan_path) if plan_path else "",
        "plan_title": plan_title or "",
    }
