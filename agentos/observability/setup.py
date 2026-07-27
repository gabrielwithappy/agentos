import os
from agentos.observability.notifier import notifier
from agentos.observability.adapters.github import GithubDashboardAdapter

def setup_observability() -> None:
    if os.environ.get("OBSERVABILITY_ENABLED") == "1":
        token = os.environ.get("GITHUB_TOKEN", "")
        repo = os.environ.get("OBSERVABILITY_GITHUB_REPO", "")
        project_id = os.environ.get("OBSERVABILITY_GITHUB_PROJECT_ID", "")
        if token and repo and project_id:
            adapter = GithubDashboardAdapter(token=token, repo=repo, project_id=project_id)
            notifier.register_adapter(adapter)
