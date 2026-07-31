import logging
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from pathlib import Path
from agentos.observability.notifier import DashboardAdapter
from agentos.observability.plan_parser import parse_exec_plan, render_card_body, upsert_meta_field

logger = logging.getLogger(__name__)

_GRAPHQL_URL = "https://api.github.com/graphql"

_IGNORED_EVENTS = {"FILE_WRITTEN", "CLI_EOF", "CLI_EXIT", "CLI_ERROR"}
_STATUS_BY_EVENT = {
    "CLI_INTERRUPT": "Todo",
    "TASK_BLOCKED": "Todo",
    "TASK_EXCEPTION": "Todo",
    "TASK_STATE_CHANGED": "In Progress",
    "TASK_COMPLETED": "Done",
}
_DEFAULT_STATUS = "Todo"


class GithubDashboardAdapter(DashboardAdapter):
    """Sends observability events to a GitHub Projects v2 board via GraphQL.

    Projects v2 has no REST API (GitHub retired Classic Projects REST
    endpoints for new repos/accounts), so every call here is a GraphQL
    query/mutation against api.github.com/graphql.
    """

    def __init__(
        self,
        token: str,
        owner: str,
        project_number: str,
        status_by_event: Dict[str, str] | None = None,
    ):
        self.token = token
        self.owner = owner
        self.project_number = project_number
        self.status_by_event = status_by_event if status_by_event is not None else dict(_STATUS_BY_EVENT)
        self._project_id: str | None = None
        self._status_field_id: str | None = None
        self._status_option_ids: Dict[str, str] = {}
        self._item_ids: Dict[str, str] = {}

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        req = urllib.request.Request(
            _GRAPHQL_URL,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            body = json.loads(response.read())
        if body.get("errors"):
            errors = body["errors"]
            err_str = str(errors)
            if "INSUFFICIENT_SCOPES" in err_str or "read:project" in err_str or "projectV2" in err_str:
                raise ValueError(
                    "Github GraphQL error: INSUFFICIENT_SCOPES — GitHub 인증 토큰에 'project' 또는 'read:project' 권한이 없습니다. "
                    "터미널에서 'gh auth refresh -s project,read:project' (또는 'gh auth login -s project,read:project')를 실행해 권한을 부여하세요."
                )
            raise ValueError(f"Github GraphQL error: {errors}")
        return body["data"]

    def _ensure_project_metadata(self) -> None:
        if self._project_id is not None:
            return
        data = self._graphql(
            """
            query($owner: String!, $number: Int!) {
              user(login: $owner) {
                projectV2(number: $number) {
                  id
                  field(name: "Status") {
                    ... on ProjectV2SingleSelectField {
                      id
                      options { id name }
                    }
                  }
                }
              }
            }
            """,
            {"owner": self.owner, "number": int(self.project_number)},
        )
        project = data["user"]["projectV2"]
        self._project_id = project["id"]
        status_field = project["field"]
        self._status_field_id = status_field["id"]
        self._status_option_ids = {
            opt["name"]: opt["id"] for opt in status_field["options"]
        }

    def _create_draft_item(self, title: str) -> str:
        """Create a draft item and return its ProjectV2Item id (used by _set_status)."""
        return self._create_draft_item_with_content_id(title)[0]

    def _create_draft_item_with_content_id(self, title: str) -> tuple[str, str]:
        """Create a draft item, returning (ProjectV2Item id, DraftIssue content id).

        The two ids are distinct GraphQL node types: `_set_status` needs the
        ProjectV2Item id, while `update_draft_issue_body` needs the DraftIssue
        content id. Conflating them fails silently against the API.
        """
        data = self._graphql(
            """
            mutation($projectId: ID!, $title: String!) {
              addProjectV2DraftIssue(input: {projectId: $projectId, title: $title}) {
                projectItem {
                  id
                  content { ... on DraftIssue { id } }
                }
              }
            }
            """,
            {"projectId": self._project_id, "title": title},
        )
        project_item = data["addProjectV2DraftIssue"]["projectItem"]
        return project_item["id"], project_item["content"]["id"]

    def _set_status(self, item_id: str, option_id: str) -> None:
        self._graphql(
            """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId,
                itemId: $itemId,
                fieldId: $fieldId,
                value: {singleSelectOptionId: $optionId}
              }) {
                projectV2Item { id }
              }
            }
            """,
            {
                "projectId": self._project_id,
                "itemId": item_id,
                "fieldId": self._status_field_id,
                "optionId": option_id,
            },
        )

    def find_item_by_title(self, title: str) -> str | None:
        """Look up an existing draft issue's content id by board item title.

        Returns the DraftIssue content id (needed by
        ``update_draft_issue_body``), not the ProjectV2Item id. Queries a
        single page of up to 100 items — appropriate for a single-owner,
        low-volume board. Raises if the board has more than that; does not
        paginate. If multiple items share the same title, returns the
        first match and logs a warning (no auto-merge/delete).
        """
        match = self._find_item_by_title_with_project_item_id(title)
        return match[1] if match else None

    def _find_item_by_title_with_project_item_id(self, title: str) -> tuple[str, str] | None:
        """Same lookup as find_item_by_title, also returning the ProjectV2Item id
        (needed by _set_status, distinct from the DraftIssue content id)."""
        self._ensure_project_metadata()
        data = self._graphql(
            """
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  items(first: 100) {
                    totalCount
                    nodes {
                      id
                      content { ... on DraftIssue { id title } }
                    }
                  }
                }
              }
            }
            """,
            {"projectId": self._project_id},
        )
        items = data["node"]["items"]
        if items["totalCount"] > 100:
            raise ValueError(
                f"Github board has more than 100 items ({items['totalCount']}); "
                "find_item_by_title does not support pagination."
            )
        matches = [
            (node["id"], node["content"]["id"])
            for node in items["nodes"]
            if node.get("content") and node["content"].get("title") == title
        ]
        if len(matches) > 1:
            logger.warning(
                f"[Observability] Multiple board items share title {title!r}; using first match."
            )
        return matches[0] if matches else None

    def update_draft_issue_body(self, draft_issue_id: str, title: str, body: str) -> None:
        self._graphql(
            """
            mutation($draftIssueId: ID!, $title: String!, $body: String!) {
              updateProjectV2DraftIssue(input: {draftIssueId: $draftIssueId, title: $title, body: $body}) {
                draftIssue { id }
              }
            }
            """,
            {"draftIssueId": draft_issue_id, "title": title, "body": body},
        )

    def _render_writing_started_body(self, payload: dict) -> str:
        lines = [
            "## 사용자 요청",
            payload.get("user_request") or "(없음)",
            "",
            "## 담당 에이전트 / 세션",
            f"- agent: {payload.get('agent') or '(없음)'}",
            f"- session: {payload.get('session') or '(없음)'}",
            "",
            "## 상태",
            "- 계획 문서 작성 중 (Backlog — Gate 2 리뷰 전)",
            "",
            "## 참조",
            f"exec-plan: {payload.get('plan_path') or '(작성 중)'}",
        ]
        return "\n".join(lines)

    async def send_notification(self, payload: Dict[str, Any]) -> None:
        if not self.token or not self.owner or not self.project_number:
            return

        event = payload.get("event", "unknown")
        if event in _IGNORED_EVENTS:
            logger.debug(f"[Observability] Ignoring telemetry event: {event}")
            return

        logger.debug(f"[Observability] Github adapter sending payload: {payload}")

        try:
            if event == "PLAN_WRITING_STARTED":
                self._ensure_project_metadata()
                title = payload.get("plan_title") or payload.get("plan_path") or payload.get("event", "계획 작성 중")
                body = self._render_writing_started_body(payload)
                existing = self._find_item_by_title_with_project_item_id(title)
                if existing is None:
                    project_item_id, draft_issue_id = self._create_draft_item_with_content_id(title=title)
                else:
                    project_item_id, draft_issue_id = existing
                self.update_draft_issue_body(draft_issue_id, title, body)
                option_id = self._status_option_ids.get("Backlog")
                if option_id is not None:
                    self._set_status(project_item_id, option_id)

            elif event == "PLAN_STATUS_CHANGED":
                self._ensure_project_metadata()
                plan_path = payload["plan_path"]
                text = Path(plan_path).read_text(encoding="utf-8")
                summary = parse_exec_plan(text)
                
                title = summary.title
                body = render_card_body(summary, plan_path)
                board_status = payload["board_status"]
                
                existing = self._find_item_by_title_with_project_item_id(title)
                if existing is None:
                    project_item_id, draft_issue_id = self._create_draft_item_with_content_id(title=title)
                else:
                    project_item_id, draft_issue_id = existing
                self.update_draft_issue_body(draft_issue_id, title, body)
                
                option_id = self._status_option_ids.get(board_status)
                if option_id is not None:
                    self._set_status(project_item_id, option_id)
                else:
                    logger.warning(
                        f"Status option '{board_status}' not found on board — "
                        "card created/updated but status not set. Run Milestone 3's board setup first."
                    )
                
                if summary.dashboard_item_id != project_item_id:
                    updated_text = upsert_meta_field(text, "dashboard_item_id", project_item_id)
                    Path(plan_path).write_text(updated_text, encoding="utf-8")

            else:
                status_name = self.status_by_event.get(event, _DEFAULT_STATUS)
                self._ensure_project_metadata()

                item_key = str(payload.get("task_id") or event)
                item_id = self._item_ids.get(item_key)
                if item_id is None:
                    item_id = self._create_draft_item(title=event)
                    self._item_ids[item_key] = item_id

                option_id = self._status_option_ids.get(status_name)
                if option_id is not None:
                    self._set_status(item_id, option_id)
        except (urllib.error.URLError, ValueError, KeyError) as e:
            raise ValueError(f"Github API error: {e}")
