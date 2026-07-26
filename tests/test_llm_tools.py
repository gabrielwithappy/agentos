from __future__ import annotations

from pathlib import Path
from typing import get_args

from agentos.llm.tools.paths import resolve_within_cwd, truncate_output
from agentos.llm.tools.registry import (
    ToolName,
    execute_tool,
    get_tool_schemas,
    requires_confirmation,
)


def test_resolve_within_cwd_blocks_escapes(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    (cwd / "inside.txt").write_text("ok", encoding="utf-8")

    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    # Plain containment.
    assert resolve_within_cwd("inside.txt", cwd) == (cwd / "inside.txt").resolve()

    # Traversal and absolute paths that leave cwd.
    assert resolve_within_cwd("../outside.txt", cwd) is None
    assert resolve_within_cwd(str(outside), cwd) is None

    # A symlink inside cwd whose target lives outside must not slip through:
    # the check resolves first, then tests containment.
    link = cwd / "link.txt"
    link.symlink_to(outside)
    assert resolve_within_cwd("link.txt", cwd) is None

    # `allowed_paths` is an explicit escape hatch and wins over containment.
    assert resolve_within_cwd(str(outside), cwd, allowed_paths=(outside,)) == outside.resolve()

    # `blocked_roots` denies even paths that are inside cwd.
    blocked = cwd / "skills"
    blocked.mkdir()
    (blocked / "SKILL.md").write_text("x", encoding="utf-8")
    assert resolve_within_cwd("skills/SKILL.md", cwd, blocked_roots=(blocked,)) is None


def test_truncate_output_caps_bytes_not_characters():
    text, truncated = truncate_output("hello", 100)
    assert (text, truncated) == ("hello", False)

    text, truncated = truncate_output("a" * 200, 50)
    assert truncated is True
    assert len(text.encode("utf-8")) <= 50

    # A cut through a multi-byte character drops it rather than raising.
    text, truncated = truncate_output("한글" * 50, 7)
    assert truncated is True
    assert len(text.encode("utf-8")) <= 7


def _tree(root: Path) -> None:
    (root / "pkg").mkdir()
    (root / "pkg" / "mod.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    (root / "pkg" / "other.txt").write_text("no match here\n", encoding="utf-8")
    (root / "top.py").write_text("alpha = 2\n", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("alpha\n", encoding="utf-8")


def test_list_glob_grep_stay_inside_cwd(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    _tree(cwd)
    outside = tmp_path / "outside.txt"
    outside.write_text("alpha secret\n", encoding="utf-8")

    listed = execute_tool("list", {}, cwd=cwd)
    assert not listed.is_error
    assert "pkg/" in listed.content and "top.py" in listed.content
    assert ".git" not in listed.content

    assert execute_tool("list", {"path": ".."}, cwd=cwd).is_error

    globbed = execute_tool("glob", {"pattern": "**/*.py"}, cwd=cwd)
    assert not globbed.is_error
    assert "top.py" in globbed.content and "pkg/mod.py" in globbed.content
    assert "other.txt" not in globbed.content

    grepped = execute_tool("grep", {"pattern": "alpha"}, cwd=cwd)
    assert not grepped.is_error
    # Matches inside cwd are reported; .git is skipped and the outside file
    # is unreachable no matter what it contains.
    assert "top.py" in grepped.content
    assert "outside.txt" not in grepped.content
    assert ".git" not in grepped.content

    assert execute_tool("grep", {"pattern": "alpha", "path": ".."}, cwd=cwd).is_error


def test_grep_reports_invalid_regex_as_error(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    _tree(cwd)
    # A model guessing a bad pattern must get a correctable tool error, not
    # an exception that kills the turn.
    result = execute_tool("grep", {"pattern": "a(b"}, cwd=cwd)
    assert result.is_error
    assert "invalid regex" in result.content


def test_readonly_tools_require_no_confirmation():
    assert set(get_args(ToolName)) == {"read", "list", "glob", "grep", "write", "edit", "bash"}
    for name in ("read", "list", "glob", "grep"):
        assert requires_confirmation(name) is False, name
    for name in ("write", "edit", "bash"):
        assert requires_confirmation(name) is True, name
    schemas = {schema["name"] for schema in get_tool_schemas(list(get_args(ToolName)))}
    assert schemas == set(get_args(ToolName))


def test_write_creates_file_inside_cwd_only(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()

    created = execute_tool("write", {"path": "new.txt", "content": "hello"}, cwd=cwd)
    assert not created.is_error
    assert "Created" in created.content
    assert (cwd / "new.txt").read_text(encoding="utf-8") == "hello"

    overwritten = execute_tool("write", {"path": "new.txt", "content": "bye"}, cwd=cwd)
    assert not overwritten.is_error
    assert "Overwrote" in overwritten.content
    assert (cwd / "new.txt").read_text(encoding="utf-8") == "bye"


def test_edit_requires_unique_match(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    target = cwd / "f.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")

    ambiguous = execute_tool(
        "edit", {"path": "f.txt", "old_string": "one", "new_string": "1"}, cwd=cwd
    )
    assert ambiguous.is_error
    assert "2 times" in ambiguous.content
    # A non-unique match must leave the file untouched.
    assert target.read_text(encoding="utf-8") == "one\ntwo\none\n"

    missing = execute_tool(
        "edit", {"path": "f.txt", "old_string": "nope", "new_string": "x"}, cwd=cwd
    )
    assert missing.is_error

    ok = execute_tool("edit", {"path": "f.txt", "old_string": "two", "new_string": "2"}, cwd=cwd)
    assert not ok.is_error
    assert target.read_text(encoding="utf-8") == "one\n2\none\n"


def test_write_and_edit_reject_paths_outside_cwd(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("original", encoding="utf-8")

    denied = execute_tool("write", {"path": "../outside.txt", "content": "pwned"}, cwd=cwd)
    assert denied.is_error
    assert outside.read_text(encoding="utf-8") == "original"

    denied = execute_tool(
        "edit",
        {"path": str(outside), "old_string": "original", "new_string": "pwned"},
        cwd=cwd,
    )
    assert denied.is_error
    assert outside.read_text(encoding="utf-8") == "original"


def test_bash_runs_in_session_cwd(tmp_path):
    cwd = tmp_path / "work"
    cwd.mkdir()
    (cwd / "marker.txt").write_text("x", encoding="utf-8")

    result = execute_tool("bash", {"command": "ls"}, cwd=cwd)
    assert not result.is_error
    assert "marker.txt" in result.content
    assert "exit=0" in result.content

    failing = execute_tool("bash", {"command": "exit 3"}, cwd=cwd)
    assert failing.is_error
    assert "exit=3" in failing.content


def test_bash_times_out_and_reports_error(tmp_path):
    result = execute_tool("bash", {"command": "sleep 5", "timeout": 1}, cwd=tmp_path)
    assert result.is_error
    assert "timed out" in result.content


def test_bash_truncates_and_redacts_output(tmp_path):
    from agentos.llm.tools.bash import MAX_OUTPUT_BYTES

    result = execute_tool(
        "bash", {"command": f"python3 -c \"print('a' * {MAX_OUTPUT_BYTES * 2})\""}, cwd=tmp_path
    )
    assert result.truncated
    assert "truncated" in result.content
    assert len(result.content.encode("utf-8")) < MAX_OUTPUT_BYTES * 2


def test_approval_screen_shows_full_bash_command_and_overwrite_state(tmp_path):
    """The approval text must never head-truncate: the tail of a command
    chain is exactly where a destructive step tends to live."""
    from agentos.llm.tools.approval import approval_prompt, describe_tool_call

    long_command = "echo " + "x" * 400 + " && rm -rf build/"
    body = describe_tool_call("bash", {"command": long_command}, cwd=tmp_path)
    assert "&& rm -rf build/" in body, "the destructive tail must stay visible"
    assert "샌드박스가 아닙니다" in body

    existing = tmp_path / "already.txt"
    existing.write_text("old content", encoding="utf-8")
    overwrite = describe_tool_call(
        "write", {"path": "already.txt", "content": "new"}, cwd=tmp_path
    )
    assert "덮어씀" in overwrite
    assert str(len("old content")) in overwrite

    creation = describe_tool_call("write", {"path": "brand-new.txt", "content": "x"}, cwd=tmp_path)
    assert "새로 만듦" in creation

    edited = describe_tool_call(
        "edit", {"path": "a.txt", "old_string": "before", "new_string": "after"}, cwd=tmp_path
    )
    assert "before" in edited and "after" in edited

    # The per-turn counter is what lets a user notice a run of prompts.
    assert "3번째" in approval_prompt("bash", {"command": "ls"}, cwd=tmp_path, call_number=3)


def test_cli_and_tui_use_the_same_approval_summary(tmp_path):
    """The CLI used to print only `arguments["path"]`, so a bash call showed
    an empty string where the command should be."""
    import inspect

    from agentos.terminal import interaction
    from agentos.terminal.tui import app as tui_app

    assert "approval_prompt" in inspect.getsource(interaction._confirm_tool_call)
    assert "approval_prompt" in inspect.getsource(tui_app.AgentOSTui.run_stream)

    from agentos.llm.tools.approval import describe_tool_call

    body = describe_tool_call("bash", {"command": "git push --force"}, cwd=tmp_path)
    assert "git push --force" in body


def test_denied_and_limit_messages_state_outcome_and_next_step():
    """Both strings are shared by the TUI and the CLI, so they are asserted
    on the renderer directly rather than through a TUI fixture."""
    from agentos.terminal.tui.renderers import render_event

    denied = render_event({"type": "tool_call_denied", "metadata": {"name": "write"}})
    assert "종료" in denied
    assert "변경되지 않았습니다" in denied
    assert "Next:" in denied

    limited = render_event({"type": "tool_call_limit_reached", "metadata": {"limit": 10}})
    assert "종료" in limited
    assert "Next:" in limited
