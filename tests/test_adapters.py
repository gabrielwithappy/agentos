import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from agentos.observability.adapters.github import GithubDashboardAdapter


def _mock_response(body: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(body).encode("utf-8")
    return mock_response


def _project_metadata_response():
    return {
        "data": {
            "user": {
                "projectV2": {
                    "id": "PVT_test",
                    "field": {
                        "id": "PVTSSF_test",
                        "options": [
                            {"id": "opt_todo", "name": "Todo"},
                            {"id": "opt_inprogress", "name": "In Progress"},
                            {"id": "opt_done", "name": "Done"},
                        ],
                    },
                }
            }
        }
    }


def test_github_adapter_creates_draft_item_and_sets_status():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    payload = {"event": "CLI_INTERRUPT"}

    responses = [
        _project_metadata_response(),
        {"data": {"addProjectV2DraftIssue": {"projectItem": {"id": "item_1", "content": {"id": "DI_item_1"}}}}},
        {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "item_1"}}}},
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
            for r in responses
        ]

        asyncio.run(adapter.send_notification(payload))

        assert mock_urlopen.call_count == 3
        first_req = mock_urlopen.call_args_list[0][0][0]
        assert first_req.full_url == "https://api.github.com/graphql"
        assert first_req.headers["Authorization"] == "Bearer fake-token"

        draft_body = json.loads(mock_urlopen.call_args_list[1][0][0].data.decode("utf-8"))
        assert "addProjectV2DraftIssue" in draft_body["query"]

        status_body = json.loads(mock_urlopen.call_args_list[2][0][0].data.decode("utf-8"))
        assert "updateProjectV2ItemFieldValue" in status_body["query"]
        assert status_body["variables"]["optionId"] == "opt_todo"


@pytest.mark.parametrize(
    "event,expected_option_id",
    [
        ("CLI_INTERRUPT", "opt_todo"),
        ("TASK_STATE_CHANGED", "opt_inprogress"),
        ("TASK_COMPLETED", "opt_done"),
        ("SOME_UNKNOWN_EVENT", "opt_todo"),
    ],
)
def test_github_adapter_status_mapping(event, expected_option_id):
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    payload = {"event": event}

    responses = [
        _project_metadata_response(),
        {"data": {"addProjectV2DraftIssue": {"projectItem": {"id": "item_1", "content": {"id": "DI_item_1"}}}}},
        {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "item_1"}}}},
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
            for r in responses
        ]

        asyncio.run(adapter.send_notification(payload))

        status_body = json.loads(mock_urlopen.call_args_list[2][0][0].data.decode("utf-8"))
        assert status_body["variables"]["optionId"] == expected_option_id


def test_github_adapter_reuses_existing_item_for_same_key():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")

    responses = [
        _project_metadata_response(),
        {"data": {"addProjectV2DraftIssue": {"projectItem": {"id": "item_1", "content": {"id": "DI_item_1"}}}}},
        {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "item_1"}}}},
        {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "item_1"}}}},
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
            for r in responses
        ]

        asyncio.run(adapter.send_notification({"event": "CLI_INTERRUPT", "task_id": "t1"}))
        asyncio.run(adapter.send_notification({"event": "TASK_COMPLETED", "task_id": "t1"}))

        # metadata query once, draft-issue creation once, status update twice — no second draft item created.
        assert mock_urlopen.call_count == 4


def test_github_adapter_graphql_partial_failure_raises_caught_error():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    payload = {"event": "CLI_INTERRUPT"}

    error_response = {"data": None, "errors": [{"message": "Could not resolve to a ProjectV2"}]}

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = _mock_response(error_response)

        with pytest.raises(ValueError, match="Github"):
            asyncio.run(adapter.send_notification(payload))


def test_github_adapter_insufficient_scopes_error_guidance():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    payload = {"event": "CLI_INTERRUPT"}

    error_response = {"data": None, "errors": [{"type": "INSUFFICIENT_SCOPES", "message": "requires read:project"}]}

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = _mock_response(error_response)

        with pytest.raises(ValueError, match="gh auth refresh -s project,read:project"):
            asyncio.run(adapter.send_notification(payload))


def test_github_adapter_skips_when_config_incomplete():
    adapter = GithubDashboardAdapter(token="", owner="gabrielwithappy", project_number="6")

    with patch("urllib.request.urlopen") as mock_urlopen:
        asyncio.run(adapter.send_notification({"event": "CLI_INTERRUPT"}))
        mock_urlopen.assert_not_called()


def _run_graphql(mock_urlopen, responses):
    mock_urlopen.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=_mock_response(r)), __exit__=MagicMock(return_value=False))
        for r in responses
    ]


def test_find_item_by_title_match_found():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")

    items_response = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 2,
                    "nodes": [
                        {"id": "PVTI_other", "content": {"id": "DI_other", "title": "Other Card"}},
                        {"id": "PVTI_target", "content": {"id": "DI_target", "title": "My Plan Title"}},
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [_project_metadata_response(), items_response])

        result = adapter.find_item_by_title("My Plan Title")

        assert result == "DI_target"
        query_body = json.loads(mock_urlopen.call_args_list[1][0][0].data.decode("utf-8"))
        assert "items(first: 100)" in query_body["query"]
        assert query_body["variables"]["projectId"] == "PVT_test"


def test_find_item_by_title_no_match_returns_none():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")

    items_response = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 1,
                    "nodes": [{"id": "PVTI_other", "content": {"id": "DI_other", "title": "Other Card"}}],
                }
            }
        }
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [_project_metadata_response(), items_response])

        result = adapter.find_item_by_title("Nonexistent Title")

        assert result is None


def test_find_item_by_title_duplicate_titles_returns_first_and_warns(caplog):
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")

    items_response = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 2,
                    "nodes": [
                        {"id": "PVTI_first", "content": {"id": "DI_first", "title": "Dup Title"}},
                        {"id": "PVTI_second", "content": {"id": "DI_second", "title": "Dup Title"}},
                    ],
                }
            }
        }
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [_project_metadata_response(), items_response])

        with caplog.at_level("WARNING"):
            result = adapter.find_item_by_title("Dup Title")

        assert result == "DI_first"
        assert any("Dup Title" in record.message for record in caplog.records)


def test_find_item_by_title_over_100_items_raises():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")

    items_response = {"data": {"node": {"items": {"totalCount": 101, "nodes": []}}}}

    with patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [_project_metadata_response(), items_response])

        with pytest.raises(ValueError, match="pagination"):
            adapter.find_item_by_title("Anything")


def test_update_draft_issue_body_sends_correct_mutation():
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    adapter._project_id = "PVT_test"

    with patch("urllib.request.urlopen") as mock_urlopen:
        _run_graphql(mock_urlopen, [{"data": {"updateProjectV2DraftIssue": {"draftIssue": {"id": "DI_target"}}}}])

        adapter.update_draft_issue_body("DI_target", "My Plan Title", "body text")

        req_body = json.loads(mock_urlopen.call_args_list[0][0][0].data.decode("utf-8"))
        assert "updateProjectV2DraftIssue" in req_body["query"]
        assert req_body["variables"] == {
            "draftIssueId": "DI_target",
            "title": "My Plan Title",
            "body": "body text",
        }


@pytest.mark.parametrize("ignored_event", ["FILE_WRITTEN", "CLI_EOF", "CLI_EXIT", "CLI_ERROR"])
def test_github_adapter_ignores_file_written_event(ignored_event):
    adapter = GithubDashboardAdapter(token="fake-token", owner="gabrielwithappy", project_number="6")
    payload = {"event": ignored_event, "path": "/some/path/file.py", "bytes": 100}

    with patch("urllib.request.urlopen") as mock_urlopen:
        asyncio.run(adapter.send_notification(payload))
        assert mock_urlopen.call_count == 0


def test_github_adapter_custom_status_by_event_mapping():
    custom_mapping = {"CUSTOM_EVENT": "In Progress"}
    adapter = GithubDashboardAdapter(
        token="fake-token", owner="owner", project_number="1", status_by_event=custom_mapping
    )
    assert adapter.status_by_event["CUSTOM_EVENT"] == "In Progress"


def test_load_adapters_from_config():
    from agentos.observability.notifier import notifier
    with patch("agentos.observability.setup.setup_observability") as mock_setup:
        notifier.load_adapters_from_config()
        assert mock_setup.called


