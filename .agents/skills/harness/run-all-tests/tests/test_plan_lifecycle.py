import json
import subprocess
from pathlib import Path
from typing import Optional

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "writing-plans" / "scripts" / "plan_lifecycle.py"


def write_plan(
    path: Path,
    title: str,
    status: str,
    reviewed: bool = False,
    user_outcome: Optional[str] = None,
    progress: Optional[str] = None,
    korean_labels: bool = False,
) -> None:
    reviewed_line = "> reviewed: true\n" if reviewed else ""
    outcome_label = "사용자 결과" if korean_labels else "User-Visible Outcome"
    progress_label = "진행 상태" if korean_labels else "Progress"
    outcome_line = f"**{outcome_label}:** {user_outcome}\n" if user_outcome else ""
    progress_line = f"**{progress_label}:** {progress}\n" if progress else ""
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"> **상태:** {status}",
                "> **작성일:** 2026-04-10",
                reviewed_line.rstrip(),
                "",
                outcome_line.rstrip(),
                "",
                progress_line.rstrip(),
                "",
                "Body",
                "",
            ]
        ).replace("\n\n\n", "\n\n"),
        encoding="utf-8",
    )


def run_cli(tmp_path: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args, "--root", str(tmp_path)],
        check=check,
        capture_output=True,
        text=True,
    )


def test_refresh_generates_plan_json_and_board(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    archive = exec_plans / "archive"
    reference = archive / "reference"
    reference.mkdir(parents=True)
    active = exec_plans / "active"
    active.mkdir(parents=True)

    write_plan(active / "2026-04-10-active.md", "Active Plan", "구현 계획 (실행 대기)", reviewed=True)
    write_plan(reference / "2026-04-10-reference.md", "Reference Plan", "계획 초안")
    write_plan(archive / "2026-04-10-archived.md", "Archived Plan", "완료", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in plan["active_plans"]] == ["docs/exec-plans/active/2026-04-10-active.md"]
    assert [item["path"] for item in plan["reference_plans"]] == ["docs/exec-plans/archive/reference/2026-04-10-reference.md"]
    assert [item["path"] for item in plan["archived_plans"]] == ["docs/exec-plans/archive/2026-04-10-archived.md"]
    assert plan["archived_summary"] == {"completed": 1, "parked": 0}
    assert plan["active_plans"][0].get("reviewed_header") is True
    assert "reviewed" not in plan["reference_plans"][0]
    assert plan["current_plan"] is None

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "## Active Plans" in readme
    assert "## Archived Plans" in readme
    assert "## Reference Docs" in readme
    assert "- 현재 실행 중인 계획 없음" not in readme
    assert "- 현재 실행 중:" not in readme
    assert "- archive summary: completed=1, parked=0" in readme
    assert "- older active plans omitted=0" in readme
    assert "- older archived plans omitted=0" in readme
    assert "- older reference docs omitted=0" in readme
    assert "[Active Plan](docs/exec-plans/active/2026-04-10-active.md)" in readme
    assert "[Reference Plan](docs/exec-plans/archive/reference/2026-04-10-reference.md)" in readme
    assert "[Archived Plan](docs/exec-plans/archive/2026-04-10-archived.md)" in readme
    assert "## 참고 계획" not in readme


def test_refresh_projects_user_outcome_and_progress(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    active = tmp_path / "docs" / "exec-plans" / "active"
    active.mkdir(parents=True)

    write_plan(
        active / "2026-04-10-active.md",
        "Active Plan",
        "구현 계획 (실행 대기)",
        reviewed=True,
        user_outcome="사용자는 계획 상단과 board에서 최종 결과를 바로 확인한다.",
        progress="Execution-ready - waiting for Task 0.",
    )
    write_plan(active / "2026-04-10-legacy.md", "Legacy Plan", "구현 계획 (실행 대기)", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    active_by_title = {item["title"]: item for item in plan["active_plans"]}
    assert active_by_title["Active Plan"]["user_outcome"] == "사용자는 계획 상단과 board에서 최종 결과를 바로 확인한다."
    assert active_by_title["Active Plan"]["progress"] == "Execution-ready - waiting for Task 0."
    assert "user_outcome" not in active_by_title["Legacy Plan"]
    assert "progress" not in active_by_title["Legacy Plan"]

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "outcome: 사용자는 계획 상단과 board에서 최종 결과를 바로 확인한다." in readme
    assert "progress: Execution-ready - waiting for Task 0." in readme
    assert "[Legacy Plan](docs/exec-plans/active/2026-04-10-legacy.md) | reviewed" in readme


def test_refresh_projects_korean_user_outcome_and_progress(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    active = tmp_path / "docs" / "exec-plans" / "active"
    active.mkdir(parents=True)

    write_plan(
        active / "2026-04-10-korean.md",
        "한국어 계획",
        "구현 계획 (실행 대기)",
        reviewed=True,
        user_outcome="사용자는 한국어 계획 요약을 board에서 바로 확인한다.",
        progress="실행 대기 - Task 0 준비 중.",
        korean_labels=True,
    )

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    entry = plan["active_plans"][0]
    assert entry["user_outcome"] == "사용자는 한국어 계획 요약을 board에서 바로 확인한다."
    assert entry["progress"] == "실행 대기 - Task 0 준비 중."

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "outcome: 사용자는 한국어 계획 요약을 board에서 바로 확인한다." in readme
    assert "progress: 실행 대기 - Task 0 준비 중." in readme


def test_refresh_uses_loop_state_for_current_plan(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: "docs/exec-plans/active/2026-04-10-active.md"\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active_dir = exec_plans / "active"
    active_dir.mkdir(parents=True)

    plan_path = active_dir / "2026-04-10-active.md"
    write_plan(plan_path, "Active Plan", "구현 계획 (실행 대기)", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert plan["current_plan"] == "docs/exec-plans/active/2026-04-10-active.md"
    assert plan["active_plans"][0]["status"] == "구현 계획 (실행 대기)"
    assert "current_plan_warning" not in plan

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- 현재 실행 중: `docs/exec-plans/active/2026-04-10-active.md`" in readme
    assert "plan_path mismatch" not in readme
    assert "- older active plans omitted=0" in readme


def test_refresh_keeps_review_pending_active_plan_in_active_registry(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active_dir = exec_plans / "active"
    active_dir.mkdir(parents=True)

    write_plan(active_dir / "2026-04-10-review-pending.md", "Review Pending Plan", "구현 계획 (리뷰 대기)")

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in plan["active_plans"]] == ["docs/exec-plans/active/2026-04-10-review-pending.md"]

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "[Review Pending Plan](docs/exec-plans/active/2026-04-10-review-pending.md)" in readme
    assert "- 현재 실행 중인 계획 없음" not in readme
    assert "- older active plans omitted=0" in readme


def test_refresh_surfaces_current_plan_path_mismatch_warning(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: "docs/exec-plans/active/2026-04-10-missing.md"\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active_dir = exec_plans / "active"
    active_dir.mkdir(parents=True)

    write_plan(active_dir / "2026-04-10-active.md", "Active Plan", "구현 계획 (실행 대기)", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert plan["current_plan"] is None
    assert plan["current_plan_warning"] == {
        "type": "plan_path_mismatch",
        "plan_path": "docs/exec-plans/active/2026-04-10-missing.md",
    }

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- 현재 실행 중인 계획 없음" not in readme
    assert "plan_path mismatch" in readme
    assert "docs/exec-plans/active/2026-04-10-missing.md" in readme
    assert "- older active plans omitted=0" in readme


def test_set_status_rejects_in_progress_status(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    active_dir = tmp_path / "docs" / "exec-plans" / "active"
    active_dir.mkdir(parents=True)
    plan_path = active_dir / "2026-04-10-active.md"
    write_plan(plan_path, "Active Plan", "구현 계획 (실행 대기)", reviewed=True)

    result = run_cli(tmp_path, "set-status", "docs/exec-plans/active/2026-04-10-active.md", "진행 중", check=False)
    assert result.returncode == 1
    assert "invalid status" in result.stderr


def test_archive_moves_plan_and_reclassifies_board(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: "docs/exec-plans/active/2026-04-10-active.md"\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active_dir = exec_plans / "active"
    active_dir.mkdir(parents=True)

    plan_path = active_dir / "2026-04-10-active.md"
    write_plan(plan_path, "Active Plan", "구현 계획 (실행 대기)", reviewed=True)

    run_cli(tmp_path, "archive", "docs/exec-plans/active/2026-04-10-active.md", "--status", "완료")

    archived_path = exec_plans / "archive" / "2026-04-10-active.md"
    assert not plan_path.exists()
    assert archived_path.exists()
    assert "> **상태:** 완료" in archived_path.read_text(encoding="utf-8")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert plan["current_plan"] is None
    assert [item["path"] for item in plan["archived_plans"]] == ["docs/exec-plans/archive/2026-04-10-active.md"]

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- 현재 실행 중인 계획 없음" in readme
    assert "[Active Plan](docs/exec-plans/archive/2026-04-10-active.md)" in readme
    assert "- older archived plans omitted=0" in readme


@pytest.mark.parametrize(
        ("command", "expected_error"),
        [
            (("set-status", "docs/exec-plans/active/2026-04-10-a.md", "엉뚱한 상태"), "invalid status"),
            (("set-status", "docs/exec-plans/active/missing.md", "구현 계획 (실행 대기)"), "plan not found"),
            (("archive", "docs/exec-plans/archive/2026-04-10-archived.md", "--status", "완료"), "already archived"),
            (("archive", "docs/exec-plans/active/2026-04-10-a.md", "--status", "보관됨"), "archive only supports"),
        ],
)
def test_lifecycle_commands_reject_invalid_inputs_without_artifact_changes(tmp_path, command, expected_error):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    archive = exec_plans / "archive"
    active = exec_plans / "active"
    active.mkdir(parents=True)
    archive.mkdir(parents=True)

    write_plan(active / "2026-04-10-a.md", "Plan A", "구현 계획 (실행 대기)", reviewed=True)
    write_plan(archive / "2026-04-10-archived.md", "Archived Plan", "완료", reviewed=True)

    run_cli(tmp_path, "refresh")
    before_plan = (tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8")
    before_readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")

    result = run_cli(tmp_path, *command, check=False)

    assert result.returncode == 1
    assert expected_error in result.stderr
    assert (tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8") == before_plan
    assert (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8") == before_readme


def test_archive_rejects_destination_collision_without_artifact_changes(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    archive = exec_plans / "archive"
    active = exec_plans / "active"
    active.mkdir(parents=True)
    archive.mkdir(parents=True)

    write_plan(active / "2026-04-10-a.md", "Plan A", "구현 계획 (실행 대기)", reviewed=True)
    write_plan(archive / "2026-04-10-a.md", "Archived Plan A", "완료", reviewed=True)

    run_cli(tmp_path, "refresh")
    before_plan = (tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8")
    before_readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")

    result = run_cli(tmp_path, "archive", "docs/exec-plans/active/2026-04-10-a.md", "--status", "완료", check=False)

    assert result.returncode == 1
    assert "archive destination already exists" in result.stderr
    assert (tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8") == before_plan
    assert (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8") == before_readme


def test_refresh_keeps_reference_plans_separate_from_archived(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active = exec_plans / "active"
    archive = exec_plans / "archive"
    reference = archive / "reference"
    active.mkdir(parents=True)
    reference.mkdir(parents=True)

    write_plan(active / "2026-04-10-a.md", "Plan A", "구현 계획 (실행 대기)", reviewed=True)
    write_plan(reference / "2026-04-10-b.md", "Reference Plan", "설계 문서 (구현 미정)", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in plan["reference_plans"]] == ["docs/exec-plans/archive/reference/2026-04-10-b.md"]
    assert plan["archived_plans"] == []
    assert plan["archived_summary"] == {"completed": 0, "parked": 0}

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- archive summary: completed=0, parked=0" in readme
    assert "## Reference Docs" in readme
    assert "- older reference docs omitted=0" in readme
    assert "[Reference Plan](docs/exec-plans/archive/reference/2026-04-10-b.md)" in readme


def test_refresh_generates_archived_summary_for_completed_and_parked_only(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    archive = exec_plans / "archive"
    reference = archive / "reference"
    archive.mkdir(parents=True)
    reference.mkdir(parents=True)

    write_plan(archive / "2026-04-10-complete.md", "Complete Plan", "완료", reviewed=True)
    write_plan(archive / "2026-04-10-parked.md", "Parked Plan", "구현 계획 (실행 대기)", reviewed=True)
    write_plan(reference / "2026-04-10-reference.md", "Reference Plan", "완료", reviewed=True)

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in plan["archived_plans"]] == [
        "docs/exec-plans/archive/2026-04-10-complete.md",
        "docs/exec-plans/archive/2026-04-10-parked.md",
    ]
    assert plan["archived_summary"] == {"completed": 1, "parked": 1}

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- archive summary: completed=1, parked=1" in readme
    lines = readme.splitlines()
    idx = lines.index("## Archived Plans")
    assert lines[idx + 1] == "- archive summary: completed=1, parked=1"
    assert lines[idx + 2] == "- older archived plans omitted=0"


def test_refresh_supports_nested_reference_taxonomy(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    reference = exec_plans / "archive" / "reference" / "intent"
    reference.mkdir(parents=True)

    write_plan(reference / "intent-20260414-sample.md", "Intent Sheet", "계획 초안")

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in plan["reference_plans"]] == [
        "docs/exec-plans/archive/reference/intent/intent-20260414-sample.md"
    ]

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert "- older reference docs omitted=0" in readme
    assert "[Intent Sheet](docs/exec-plans/archive/reference/intent/intent-20260414-sample.md)" in readme


def test_refresh_compresses_board_to_recent_limits_but_keeps_full_json_lists(tmp_path):
    (tmp_path / ".agents" / "mission").mkdir(parents=True)
    traces = tmp_path / ".agents" / "traces" / "harness"
    traces.mkdir(parents=True)
    (traces / "loop-state.md").write_text('plan_path: ""\n', encoding="utf-8")
    exec_plans = tmp_path / "docs" / "exec-plans"
    active = exec_plans / "active"
    archive = exec_plans / "archive"
    reference = archive / "reference"
    active.mkdir(parents=True)
    reference.mkdir(parents=True)

    for idx in range(1, 26):
        write_plan(active / f"2026-04-{idx:02d}-active.md", f"Active {idx:02d}", "구현 계획 (실행 대기)", reviewed=True)
    for idx in range(1, 24):
        write_plan(archive / f"2026-03-{idx:02d}-archived.md", f"Archived {idx:02d}", "완료", reviewed=True)
    for idx in range(1, 13):
        write_plan(reference / f"2026-02-{idx:02d}-reference.md", f"Reference {idx:02d}", "계획 초안")

    run_cli(tmp_path, "refresh")

    plan = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert len(plan["active_plans"]) == 25
    assert len(plan["archived_plans"]) == 23
    assert len(plan["reference_plans"]) == 12

    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    active_lines = [line for line in readme.splitlines() if line.startswith("- `") and "/active/" in line]
    archived_lines = [line for line in readme.splitlines() if line.startswith("- `") and "/archive/" in line and "/reference/" not in line]
    reference_lines = [line for line in readme.splitlines() if line.startswith("- `") and "/archive/reference/" in line]
    assert len(active_lines) == 20
    assert len(archived_lines) == 20
    assert len(reference_lines) == 10
    assert "- older active plans omitted=5" in readme
    assert "- older archived plans omitted=3" in readme
    assert "- older reference docs omitted=2" in readme
    assert "Active 25" in readme
    assert "Active 05" not in readme
    assert "Archived 23" in readme
    assert "Archived 03" not in readme
    assert "Reference 12" in readme
    assert "Reference 02" not in readme
