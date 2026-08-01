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


def test_touched_paths_extracts_apply_patch_file_headers():
    payload = {
        "tool_input": {
            "command": """*** Begin Patch
*** Update File: .agentos/project/exec-plans/active/example.md
@@
+changed
*** Add File: .agentos/project/exec-plans/active/new.md
+new
*** End Patch
"""
        }
    }

    assert _touched_paths(payload) == [
        ".agentos/project/exec-plans/active/example.md",
        ".agentos/project/exec-plans/active/new.md",
    ]

def test_touched_paths_ignores_invalid_input():
    assert _touched_paths({"tool_input": "not a dict"}) == []
    assert _touched_paths({}) == []

def test_main_exits_if_not_edit_tool():
    with patch("dashboard_sync_on_plan_write._load_payload", return_value={"tool_name": "Ask"}):
        assert main() == 0

def test_main_exits_if_not_active_plan():
    with patch("dashboard_sync_on_plan_write._load_payload", return_value={"tool_name": "Edit", "tool_input": {"file_path": "random/file.md"}}):
        assert main() == 0


def test_main_accepts_apply_patch_active_plan(tmp_path):
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n*** Update File: .agentos/project/exec-plans/active/example.md\n@@\n+x\n*** End Patch\n"
        },
    }

    with patch("dashboard_sync_on_plan_write._load_payload", return_value=payload), \
         patch("dashboard_sync_on_plan_write.subprocess.run") as run:
        script = tmp_path / ".agents" / "skills" / "harness" / "writing-plans" / "scripts" / "plan_lifecycle.py"
        script.parent.mkdir(parents=True)
        script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        with patch("sys.argv", ["dashboard_sync_on_plan_write.py", str(tmp_path)]):
            assert main() == 0

    assert run.called
