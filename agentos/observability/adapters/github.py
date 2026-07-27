import logging
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from agentos.observability.notifier import DashboardAdapter

logger = logging.getLogger(__name__)

class GithubDashboardAdapter(DashboardAdapter):
    def __init__(self, token: str, repo: str, project_id: str):
        self.token = token
        self.repo = repo
        self.project_id = project_id
        
    async def send_notification(self, payload: Dict[str, Any]) -> None:
        if not self.token or not self.repo:
            return
            
        url = f"https://api.github.com/repos/{self.repo}/projects/{self.project_id}/columns"
        logger.debug(f"[Observability] Github adapter sending payload: {payload}")
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        try:
            # This is a synchronous call but it's executed in a background thread by DashboardNotifier
            with urllib.request.urlopen(req, timeout=5) as response:
                response.read()
        except urllib.error.URLError as e:
            raise ValueError(f"Github API error: {e}")
