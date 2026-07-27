from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExecPlanSummary:
    title: str
    status: str
    reviewed: str
    active_agent: str
    active_session: str
    goal: str
    last_review_entry: str


def _find_h1(text: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _find_meta_line(text: str, label: str) -> str:
    match = re.search(rf"^>\s*\*\*{re.escape(label)}:\*\*\s*(.+?)\s*(?:<br>)?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _find_meta_field(text: str, key: str) -> str:
    match = re.search(rf"^>\s*{re.escape(key)}:\s*(.*?)\s*(?:<br>)?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _find_section(text: str, heading: str) -> str:
    match = re.search(
        rf"\*\*{re.escape(heading)}:\*\*\s*\n(.+?)(?=\n\*\*|\n---|\Z)",
        text,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _find_last_review_entry(text: str) -> str:
    match = re.search(r"^##\s*리뷰 반영 이력\s*\n(.+?)(?=\n##\s|\Z)", text, re.DOTALL | re.MULTILINE)
    if not match:
        return ""
    entries = [line.strip("- ").strip() for line in match.group(1).splitlines() if line.strip().startswith("-")]
    return entries[-1] if entries else ""


def parse_exec_plan(text: str) -> ExecPlanSummary:
    return ExecPlanSummary(
        title=_find_h1(text),
        status=_find_meta_line(text, "상태"),
        reviewed=_find_meta_field(text, "reviewed"),
        active_agent=_find_meta_field(text, "active_agent"),
        active_session=_find_meta_field(text, "active_session"),
        goal=_find_section(text, "목표"),
        last_review_entry=_find_last_review_entry(text),
    )


def status_to_board_status(status_text: str, reviewed: str) -> str:
    """Map an exec-plan's status text + reviewed field to a 4-stage board status.

    판단 순서 (계획 문서 아키텍처 섹션 참고):
    1. 주 상태 문구(괄호 앞)가 "완료"로 시작하면 → Done.
    2. 그 외 reviewed가 true가 아니면 → Backlog (Gate 2 리뷰 미통과).
    3. reviewed가 true이고 주 상태 문구에 "완료"가 없으면 → Ready.
    4. 나머지(reviewed true + "완료"가 주 상태 문구에 있지만 "완료"로 시작하지
       않는 경우, 예: "구현 완료") → In Progress.
    """
    primary_status = status_text.split("(", 1)[0].strip()
    is_reviewed = reviewed.strip().lower().startswith("true")

    if primary_status.startswith("완료"):
        return "Done"
    if not is_reviewed:
        return "Backlog"
    if "완료" not in primary_status:
        return "Ready"
    return "In Progress"


def render_card_body(summary: ExecPlanSummary, plan_path: str) -> str:
    lines = [
        f"## 목표\n{summary.goal}" if summary.goal else "## 목표\n(없음)",
        "\n## 상태",
        f"- {summary.status}" if summary.status else "- (없음)",
        "\n## 담당 에이전트 / 세션",
        f"- active_agent: {summary.active_agent}" if summary.active_agent else "- active_agent: (없음)",
        f"- active_session: {summary.active_session}" if summary.active_session else "- active_session: (없음)",
        "\n## 최근 리뷰 이력",
        f"- {summary.last_review_entry}" if summary.last_review_entry else "- (없음)",
        "\n## 참조",
        f"exec-plan: {plan_path}",
    ]
    return "\n".join(lines)
