from pathlib import Path

from agentos.observability.plan_parser import parse_exec_plan, status_to_board_status

REAL_PLAN_PATH = Path(
    ".agentos/project/exec-plans/active/2026-07-27-github-projectv2-dashboard-adapter.md"
)


def test_parses_real_exec_plan_title_and_status():
    text = REAL_PLAN_PATH.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)

    assert summary.title == "GitHub Projects v2(GraphQL) 대시보드 어댑터 교체 구현 계획"
    assert "구현 및 전체 검증 완료" in summary.status


def test_parses_real_exec_plan_agent_and_session():
    text = REAL_PLAN_PATH.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)

    assert summary.active_agent == "Claude Code (claude-sonnet-5)"
    assert summary.active_session == "5b17931b-4ac1-4a97-9600-9b13d78e9f7f"


def test_parses_real_exec_plan_goal_and_last_review_entry():
    text = REAL_PLAN_PATH.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)

    assert "Classic Projects REST" in summary.goal
    assert "2차 리뷰" in summary.last_review_entry


def test_parses_reviewed_field():
    text = REAL_PLAN_PATH.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)

    assert summary.reviewed.startswith("true")


def test_missing_fields_return_empty_string():
    text = "# 제목만 있는 계획\n\n내용 없음\n"
    summary = parse_exec_plan(text)

    assert summary.title == "제목만 있는 계획"
    assert summary.status == ""
    assert summary.active_agent == ""
    assert summary.goal == ""


def test_status_to_board_status_real_backlog_cases():
    # reviewed: false — 저장소 실존 사례
    assert status_to_board_status("구현 계획 (리뷰 대기)", "false") == "Backlog"
    assert status_to_board_status("리뷰 대기 (완료 후 '완료'로 변경)", "false") == "Backlog"


def test_status_to_board_status_real_needs_context_maps_to_ready():
    # NEEDS_CONTEXT (분석 handoff 완료) — reviewed: true이고 주 상태 문구에
    # "완료"가 없는(괄호 안에만 있음) 저장소 유일의 실존 Ready 사례.
    assert status_to_board_status("NEEDS_CONTEXT (분석 handoff 완료)", "true") == "Ready"


def test_status_to_board_status_virtual_ready_example():
    # 저장소에 실존하지 않는 가상 예시 — reviewed: true + 주 상태에 "완료" 없음.
    assert status_to_board_status("구현 대기 (Gate 2 리뷰 통과, 완료 후 '완료'로 변경)", "true") == "Ready"


def test_status_to_board_status_real_in_progress_cases():
    assert status_to_board_status("구현 완료", "true") == "In Progress"
    assert status_to_board_status("구현 및 전체 검증 완료 (사용자 실사용 확인 대기)", "true") == "In Progress"


def test_status_to_board_status_real_done_cases():
    assert status_to_board_status("완료", "true") == "Done"
    assert status_to_board_status("완료 (Scope Exception 승인됨)", "true") == "Done"
    assert status_to_board_status("완료 (구현·검증 완료)", "true") == "Done"


def test_status_to_board_status_unknown_text_falls_back_to_ready():
    # 8종류 조합 밖의 완전히 새로운 문구 — reviewed:false여도 규칙 (2)가
    # 먼저 걸려 Backlog가 되므로, 진짜 폴백은 reviewed:true인 미지 문구에서만 발생.
    assert status_to_board_status("전혀 새로운 미지의 상태 문구", "true") == "Ready"
