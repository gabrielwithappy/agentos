import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(".agents/hooks/scripts"))
from dashboard_sync_on_plan_write import _touched_paths, main

def test_touched_paths_aliases():
    assert _touched_paths({"tool_input": {"file_path": "a.md"}}) == ["a.md"]
    assert _touched_paths({"tool_input": {"path": "b.md"}}) == ["b.md"]
    assert _touched_paths({"tool_input": {"target_file": "c.md"}}) == ["c.md"]

def test_touched_paths_ignores_invalid_input():
    assert _touched_paths({"tool_input": "not a dict"}) == []
    assert _touched_paths({}) == []

def test_main_exits_if_not_edit_tool():
    with patch("dashboard_sync_on_plan_write._load_payload", return_value={"tool_name": "Ask"}):
        assert main() == 0

def test_main_exits_if_not_active_plan():
    with patch("dashboard_sync_on_plan_write._load_payload", return_value={"tool_name": "Edit", "tool_input": {"file_path": "random/file.md"}}):
        assert main() == 0
