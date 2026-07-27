from agentos.observability.plan_parser import parse_exec_plan, status_to_board_status

# 실제 exec-plan 파일(2026-07-27-github-projectv2-dashboard-adapter.md)의
# 헤더/목표/리뷰 이력 구조를 그대로 옮긴 고정 픽스처. 이 파일을 직접
# 읽으면 .gitignore된 로컬 전용 exec-plan이라 CI 환경에는 존재하지 않아
# 실패하므로(FileNotFoundError), 실제 파일 구조를 인라인 문자열로 고정한다.
SAMPLE_PLAN_TEXT = """# GitHub Projects v2(GraphQL) 대시보드 어댑터 교체 구현 계획

> **상태:** 구현 및 전체 검증 완료 (사용자 실사용 확인 대기)
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 2종 PASS, 증거: `.agents/traces/reviews/2026-07-27-github-projectv2-dashboard-adapter/{plan-reviewer,principle-auditor}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: 5b17931b-4ac1-4a97-9600-9b13d78e9f7f<br>
> implementation_started_at: 2026-07-27T09:30:00Z<br>
> implementation_completed_at: 2026-07-27T09:55:00Z<br>
> implementation_duration: 약 25분<br>

**목표:**
- 기존 `GithubDashboardAdapter`(REST `/repos/{repo}/projects/{project_id}/columns`, Classic Projects API)는 GitHub이 신규 계정/리포에서 Classic Projects REST 엔드포인트를 은퇴시켜 실제로 404로 실패한다.

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 리뷰): principle-auditor PASS, plan-reviewer FAIL.
- 2026-07-27 (Gate 2 2차 리뷰, 수정본 재검토): plan-reviewer PASS.
"""


def test_parses_real_exec_plan_title_and_status():
    summary = parse_exec_plan(SAMPLE_PLAN_TEXT)

    assert summary.title == "GitHub Projects v2(GraphQL) 대시보드 어댑터 교체 구현 계획"
    assert "구현 및 전체 검증 완료" in summary.status


def test_parses_real_exec_plan_agent_and_session():
    summary = parse_exec_plan(SAMPLE_PLAN_TEXT)

    assert summary.active_agent == "Claude Code (claude-sonnet-5)"
    assert summary.active_session == "5b17931b-4ac1-4a97-9600-9b13d78e9f7f"


def test_parses_real_exec_plan_goal_and_last_review_entry():
    summary = parse_exec_plan(SAMPLE_PLAN_TEXT)

    assert "Classic Projects REST" in summary.goal
    assert "2차 리뷰" in summary.last_review_entry


def test_parses_reviewed_field():
    summary = parse_exec_plan(SAMPLE_PLAN_TEXT)

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


def test_status_to_board_status_awaiting_verification_cases():
    # 자동 검증까지 끝났고 사람의 수동 확인만 남은 실존 문구 —
    # reviewed:true면 In Progress가 아니라 Awaiting Verification으로 분리된다.
    assert (
        status_to_board_status("구현 및 전체 검증 완료 (사용자 실사용 확인 대기)", "true")
        == "Awaiting Verification"
    )
    # reviewed 우선순위 확인: 같은 문구라도 reviewed:false면 Backlog가 먼저 걸린다.
    assert (
        status_to_board_status("구현 및 전체 검증 완료 (사용자 실사용 확인 대기)", "false")
        == "Backlog"
    )


def test_status_to_board_status_real_done_cases():
    assert status_to_board_status("완료", "true") == "Done"
    assert status_to_board_status("완료 (Scope Exception 승인됨)", "true") == "Done"
    assert status_to_board_status("완료 (구현·검증 완료)", "true") == "Done"


def test_status_to_board_status_unknown_text_falls_back_to_ready():
    # 8종류 조합 밖의 완전히 새로운 문구 — reviewed:false여도 규칙 (2)가
    # 먼저 걸려 Backlog가 되므로, 진짜 폴백은 reviewed:true인 미지 문구에서만 발생.
    assert status_to_board_status("전혀 새로운 미지의 상태 문구", "true") == "Ready"
