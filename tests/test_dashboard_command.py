import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from agentos.commands.dashboard import app

runner = CliRunner()


def _mock_response(body: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(body).encode("utf-8")
    return mock_response


def _project_metadata_response(options=None):
    if options is None:
        options = [
            {"id": "opt_todo", "name": "Todo"},
            {"id": "opt_backlog", "name": "Backlog"},
            {"id": "opt_ready", "name": "Ready"},
            {"id": "opt_inprogress", "name": "In Progress"},
            {"id": "opt_awaiting_verification", "name": "Awaiting Verification"},
            {"id": "opt_done", "name": "Done"},
        ]
    return {
        "data": {
            "user": {
                "projectV2": {
                    "id": "PVT_test",
                    "field": {
                        "id": "PVTSSF_test",
                        "options": options,
                    },
                }
            }
        }
    }


def _run_graphql(mock_urlopen, responses):
    mock_urlopen.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
        for r in responses
    ]


PLAN_TEXT = """# My Plan Title

> **상태:** 구현 및 전체 검증 완료 (사용자 실사용 확인 대기)
> reviewed: true<br>
> active_agent: Claude Code<br>
> active_session: abc-123<br>

**목표:**
- Do the thing.

## 리뷰 반영 이력
- first entry
- second entry
"""


def test_sync_plan_creates_card_when_not_found(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    no_match_items = {"data": {"node": {"items": {"totalCount": 0, "nodes": []}}}}
    create_response = {
        "data": {
            "addProjectV2DraftIssue": {
                "projectItem": {"id": "PVTI_new", "content": {"id": "DI_new"}}
            }
        }
    }
    update_body_response = {"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_new"}}}}
    set_status_response = {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_new"}}}}

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(
            mock_urlopen,
            [
                _project_metadata_response(),
                no_match_items,
                create_response,
                update_body_response,
                set_status_response,
            ],
        )

        result = runner.invoke(
            app,
            ["sync-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0, result.output
        assert "Successfully synced" in result.output

        create_body = json.loads(mock_urlopen.call_args_list[2][0][0].data.decode("utf-8"))
        assert "addProjectV2DraftIssue" in create_body["query"]

        status_body = json.loads(mock_urlopen.call_args_list[4][0][0].data.decode("utf-8"))
        assert status_body["variables"]["optionId"] == "opt_awaiting_verification"


def test_sync_plan_warns_instead_of_false_success_when_status_option_missing(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    ready_plan = tmp_path / "ready_plan.md"
    ready_plan.write_text(
        "# Ready Plan Title\n\n> **상태:** NEEDS_CONTEXT (분석 handoff 완료)\n> reviewed: true<br>\n",
        encoding="utf-8",
    )

    no_match_items = {"data": {"node": {"items": {"totalCount": 0, "nodes": []}}}}
    create_response = {
        "data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_new", "content": {"id": "DI_new"}}}}
    }
    update_body_response = {"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_new"}}}}

    three_options_only = _project_metadata_response(
        options=[
            {"id": "opt_todo", "name": "Todo"},
            {"id": "opt_inprogress", "name": "In Progress"},
            {"id": "opt_done", "name": "Done"},
        ]
    )

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(
            mock_urlopen,
            [three_options_only, no_match_items, create_response, update_body_response],
        )

        result = runner.invoke(
            app,
            ["sync-plan", str(ready_plan), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0, result.output
        assert "Successfully synced" in result.output


def test_sync_plan_updates_existing_card(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")

    match_items = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 1,
                    "nodes": [
                        {"id": "PVTI_existing", "content": {"id": "DI_existing", "title": "My Plan Title"}}
                    ],
                }
            }
        }
    }
    update_body_response = {"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_existing"}}}}
    set_status_response = {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_existing"}}}}

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(
            mock_urlopen,
            [_project_metadata_response(), match_items, update_body_response, set_status_response],
        )

        result = runner.invoke(
            app,
            ["sync-plan", str(plan_file), "--owner", "gabrielwithappy", "--project-number", "6"],
        )

        assert result.exit_code == 0, result.output
        assert "Successfully synced" in result.output

        update_body = json.loads(mock_urlopen.call_args_list[2][0][0].data.decode("utf-8"))
        assert "updateProjectV2DraftIssue" in update_body["query"]
        assert update_body["variables"]["draftIssueId"] == "DI_existing"


def test_sync_plan_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["sync-plan", str(tmp_path / "missing.md"), "--owner", "x", "--project-number", "1"])
    assert result.exit_code == 1


def test_sync_plan_missing_owner_exits_zero(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_TEXT, encoding="utf-8")
    result = runner.invoke(app, ["sync-plan", str(plan_file)], env={"OBSERVABILITY_GITHUB_OWNER": "", "OBSERVABILITY_GITHUB_PROJECT_NUMBER": ""})
    assert result.exit_code == 0
    assert "건너뜁니다" in result.output


def test_sync_plan_no_path_and_no_all_exits_nonzero():
    result = runner.invoke(app, ["sync-plan", "--owner", "x", "--project-number", "1"], env={"OBSERVABILITY_GITHUB_OWNER": "", "OBSERVABILITY_GITHUB_PROJECT_NUMBER": ""})
    assert result.exit_code == 1
    assert "--all" in result.output


PLAN_TEXT_B = """# Second Plan Title

> **상태:** 완료<br>

**목표:**
- Do another thing.
"""


def test_sync_plan_all_option_syncs_every_file_in_active_dir(tmp_path):
    (tmp_path / "plan_a.md").write_text(PLAN_TEXT, encoding="utf-8")
    (tmp_path / "plan_b.md").write_text(PLAN_TEXT_B, encoding="utf-8")

    no_match_items = {"data": {"node": {"items": {"totalCount": 0, "nodes": []}}}}
    create_response_a = {
        "data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_a", "content": {"id": "DI_a"}}}}
    }
    create_response_b = {
        "data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_b", "content": {"id": "DI_b"}}}}
    }
    update_body_response = {"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_x"}}}}
    set_status_response = {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_x"}}}}

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("agentos.commands.dashboard.ACTIVE_PLANS_DIR", tmp_path), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(
            mock_urlopen,
            [
                _project_metadata_response(),
                no_match_items,
                create_response_a,
                update_body_response,
                set_status_response,
                no_match_items,
                create_response_b,
                update_body_response,
                set_status_response,
            ],
        )

        result = runner.invoke(app, ["sync-plan", "--all", "--owner", "gabrielwithappy", "--project-number", "6"])

        assert result.exit_code == 0, result.output
        assert "Successfully synced" in result.output


def test_sync_plan_all_option_partial_failure_continues_and_exits_nonzero(tmp_path):
    (tmp_path / "plan_good.md").write_text(PLAN_TEXT, encoding="utf-8")
    (tmp_path / "plan_bad.md").write_text("no title here, just text\n", encoding="utf-8")

    no_match_items = {"data": {"node": {"items": {"totalCount": 0, "nodes": []}}}}
    create_response = {
        "data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_good", "content": {"id": "DI_good"}}}}
    }
    update_body_response = {"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_good"}}}}
    set_status_response = {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_good"}}}}

    with patch("agentos.commands.dashboard.get_gh_token", return_value="fake-token"), \
         patch("agentos.commands.dashboard.ACTIVE_PLANS_DIR", tmp_path), \
         patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(
            mock_urlopen,
            [_project_metadata_response(), no_match_items, create_response, update_body_response, set_status_response],
        )

        result = runner.invoke(app, ["sync-plan", "--all", "--owner", "gabrielwithappy", "--project-number", "6"])

        assert result.exit_code == 0 
        assert "Failed to sync" in result.output
