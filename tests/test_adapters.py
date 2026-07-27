import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from agentos.observability.adapters.github import GithubDashboardAdapter

def test_github_adapter_send_notification():
    adapter = GithubDashboardAdapter(token="fake-token", repo="gabrielwithappy/agentos", project_id="1")
    payload = {"event": "CLI_INTERRUPT"}
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        asyncio.run(adapter.send_notification(payload))
        
        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        assert req.full_url == "https://api.github.com/repos/gabrielwithappy/agentos/projects/1/columns"
        assert req.headers["Authorization"] == "Bearer fake-token"
        assert json.loads(req.data.decode("utf-8")) == payload
