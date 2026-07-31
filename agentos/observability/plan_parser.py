from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecPlanSummary:
    title: str
    status: str
    reviewed: str
    active_agent: str
    active_session: str
    dashboard_item_id: str
    goal: str
    user_result_summary: str
    progress_snapshot: str
    worktree_info: str
    last_review_entry: str
    user_request: str
    implementation_started_at: str
    implementation_completed_at: str
    implementation_duration: str


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


def _find_h2_section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s*{re.escape(heading)}\s*\n(.+?)(?=\n##\s|\Z)", text, re.DOTALL | re.MULTILINE)
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
        dashboard_item_id=_find_meta_field(text, "dashboard_item_id"),
        goal=_find_section(text, "목표"),
        user_result_summary=_find_h2_section(text, "사용자 결과 요약"),
        progress_snapshot=_find_h2_section(text, "진행 스냅샷"),
        worktree_info=_find_h2_section(text, "Worktree 정보"),
        last_review_entry=_find_last_review_entry(text),
        user_request=_find_meta_field(text, "user_request"),
        implementation_started_at=_find_meta_field(text, "implementation_started_at"),
        implementation_completed_at=_find_meta_field(text, "implementation_completed_at"),
        implementation_duration=_find_meta_field(text, "implementation_duration"),
    )


def upsert_meta_field(text: str, key: str, value: str) -> str:
    """Set a `> key: value<br>` metadata line in an exec-plan's header block.

    Updates the line in place if `key` already exists (blank or filled);
    otherwise inserts a new line directly after the `active_session:` line,
    the fixed anchor point every exec-plan header already has. Used to write
    the GitHub dashboard card's identity back onto the plan document after a
    sync, so a reader can confirm which card a plan is linked to (and vice
    versa) without re-running a title-based lookup.
    """
    field_re = re.compile(rf"^>\s*{re.escape(key)}:\s*.*$", re.MULTILINE)
    new_line = f"> {key}: {value}<br>"
    if field_re.search(text):
        return field_re.sub(new_line, text, count=1)

    anchor_re = re.compile(r"^>\s*active_session:\s*.*$", re.MULTILINE)
    match = anchor_re.search(text)
    if not match:
        return text
    insert_at = match.end()
    return text[:insert_at] + "\n" + new_line + text[insert_at:]


def status_to_board_status(status_text: str, reviewed: str) -> str:
    """Map an exec-plan's status text + reviewed field to a 5-stage board status.

    판단 순서 (계획 문서 아키텍처 섹션 참고):
    1. 주 상태 문구(괄호 앞)가 "완료"로 시작하면 → Done.
    2. 그 외 reviewed가 true가 아니면 → Backlog (Gate 2 리뷰 미통과).
    3. reviewed가 true이고 주 상태 문구에 "완료"가 없으면 → Ready.
    4. reviewed가 true이고 "완료"가 주 상태 문구에 있지만 "완료"로 시작하지
       않고, 상태 문구 전체(괄호 포함)에 "사용자 실사용 확인 대기"가
       포함되면 → Awaiting Verification (자동 검증은 끝났고 사람의 수동
       확인만 남은 상태).
    5. 나머지(예: "구현 완료") → In Progress.
    """
    primary_status = status_text.split("(", 1)[0].strip()
    is_reviewed = reviewed.strip().lower().startswith("true")

    if primary_status.startswith("완료"):
        return "Done"
    if not is_reviewed:
        return "Backlog"
    if "완료" not in primary_status:
        return "Ready"
    if "사용자 실사용 확인 대기" in status_text:
        return "Awaiting Verification"
    return "In Progress"


def render_card_body(summary: ExecPlanSummary, plan_path: str) -> str:
    lines = []
    if summary.user_request:
        lines.extend([
            "## 사용자 요청",
            summary.user_request,
            ""
        ])
    lines.extend([
        f"## 목표\n{summary.goal}" if summary.goal else "## 목표\n(없음)",
        f"\n## 사용자 결과 요약\n{summary.user_result_summary}" if summary.user_result_summary else "\n## 사용자 결과 요약\n(없음)",
        f"\n## 진행 스냅샷\n{summary.progress_snapshot}" if summary.progress_snapshot else "\n## 진행 스냅샷\n(없음)",
        "\n## 상태",
        f"- {summary.status}" if summary.status else "- (없음)",
        "\n## 담당 에이전트 / 세션",
        f"- active_agent: {summary.active_agent}" if summary.active_agent else "- active_agent: (없음)",
        f"- active_session: {summary.active_session}" if summary.active_session else "- active_session: (없음)",
    ])
    lines.extend(
        [
            "\n## 구현 시간 정보",
            f"- implementation_started_at: {summary.implementation_started_at}" if summary.implementation_started_at else "- implementation_started_at: (없음)",
            f"- implementation_completed_at: {summary.implementation_completed_at}" if summary.implementation_completed_at else "- implementation_completed_at: (없음)",
            f"- implementation_duration: {summary.implementation_duration}" if summary.implementation_duration else "- implementation_duration: (없음)",
        ]
    )
    if summary.worktree_info:
        # Worktree Decision Gate가 필요한 계획에만 있는 선택적 섹션이므로,
        # 없는 계획의 카드까지 "(없음)" placeholder로 채워 늘리지 않는다.
        lines.append(f"\n## Worktree 정보\n{summary.worktree_info}")
    clean_path = str(plan_path).lstrip("./")
    github_url = f"https://github.com/gabrielwithappy/agentOS/blob/main/{clean_path}"
    lines.extend(
        [
            "\n## 최근 리뷰 이력",
            f"- {summary.last_review_entry}" if summary.last_review_entry else "- (없음)",
            "\n## 참조",
            f"exec-plan: [{clean_path}]({github_url})",
            f"plan_id: {Path(plan_path).stem}",
            f"dashboard_item_id: {summary.dashboard_item_id}" if summary.dashboard_item_id else "dashboard_item_id: (없음)",
        ]
    )
    return "\n".join(lines)
