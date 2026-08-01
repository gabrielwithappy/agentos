import json
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from agentos.commands.dashboard import app

runner = CliRunner()

def _mock_response(body: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(body).encode("utf-8")
    return mock_response

def _run_graphql(mock_urlopen, responses):
    mock_urlopen.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
        for r in responses
    ]

PLAN_TEXT = """# My Plan Title

> **상태:** 구현 중
> reviewed: true<br>
> active_session: abc-123<br>
> dashboard_item_id: PVTI_123

**목표:**
- Do the thing.
"""

def test_pull_plan_matches(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    response = {
        "data": {
            "node": {
                "fieldValueByName": {
                    "name": "Ready"
                }
            }
        }
    }

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [response])

        result = runner.invoke(
            app,
            ["pull-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0
        assert "일치" in result.output
        
        updated_text = plan_file.read_text(encoding="utf-8")
        assert "remote_board_status: Ready" in updated_text


def test_pull_plan_mismatch(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    response = {
        "data": {
            "node": {
                "fieldValueByName": {
                    "name": "In Progress"
                }
            }
        }
    }

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [response])

        result = runner.invoke(
            app,
            ["pull-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0
        out_no_nl = result.output.replace("\n", " ")
        assert "불일치" in out_no_nl
        assert "예상=Ready" in out_no_nl
        assert "실제=In Progress" in out_no_nl


def test_pull_plan_no_dashboard_item_id(tmp_path):
    plan_file = tmp_path / "plan.md"
    text_without_id = """# Title\n\n> **상태:** 완료\n> active_session: abc-123<br>\n"""
    plan_file.write_text(text_without_id, encoding="utf-8")

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"):
        result = runner.invoke(
            app,
            ["pull-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0
        assert "dashboard_item_id가 없습니다" in result.output.replace("\n", " ")
        assert plan_file.read_text(encoding="utf-8") == text_without_id


def test_pull_plan_no_config(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    result = runner.invoke(
        app,
        ["pull-plan", str(plan_file)],
        env={"OBSERVABILITY_GITHUB_OWNER": "", "OBSERVABILITY_GITHUB_PROJECT_NUMBER": ""}
    )

    assert result.exit_code == 0
    assert "대시보드가 설정되어 있지 않아" in result.output.replace("\n", " ")


def test_pull_plan_no_remote_status(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    response = {
        "data": {
            "node": None
        }
    }

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [response])

        result = runner.invoke(
            app,
            ["pull-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0
        out_no_nl = result.output.replace("\n", " ")
        assert "보드에서 Status 값을 찾지" in out_no_nl
        assert "카드가 삭제되었거나" in out_no_nl
