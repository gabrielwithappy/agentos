# .agents/skills/harness/run-all-tests/tests/test_harness_loop.py
import sys
import gzip
import json
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute() / "core-engine"))
from harness_loop import (
    HarnessLoop,
    confirm_cli_execution,
    load_default_cli,
    main,
    has_completion_evidence,
    has_evolution_completion_evidence,
    is_harness_evolution_context,
    diagnostic_for_event,
)
from loop_state import LoopState


def write_reviewed_active_plan(
    root: Path,
    relative_path: str = "docs/exec-plans/active/2026-04-10-active.md",
    mcp_servers: str = "[]",
) -> str:
    plan_path = root / relative_path
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "# Active Plan",
                "",
                "> **상태:** 구현 계획 (실행 대기)",
                "> **작성일:** 2026-04-10",
                "> reviewed: true",
                f"> mcp_servers: {mcp_servers}",
                "",
                "Body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return relative_path


def events_path(root: Path) -> Path:
    return root / ".agents" / "traces" / "harness" / "events.jsonl"


def make_loop(tmp_path, prompt=None, cli="claude", **state_kwargs):
    default_plan = write_reviewed_active_plan(tmp_path)
    if prompt is None:
        prompt = f"{default_plan} 계획 문서를 기준으로 구현하라"
    state = LoopState(cli=cli, prompt=prompt, **state_kwargs)
    sf = tmp_path / ".agents" / "traces" / "harness" / "loop-state.md"
    hf = tmp_path / "HISTORY.md"
    sf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text("")
    state.to_file(sf)
    return HarnessLoop(state_file=sf, history_file=hf), sf


def write_mcp_render_helper(root: Path) -> Path:
    helper = root / ".agents" / "mcp" / "scripts" / "render-codex-mcp-config.py"
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "servers = []",
                "args = sys.argv[1:]",
                "index = 0",
                "while index < len(args):",
                "    if args[index] == '--server':",
                "        servers.append(args[index + 1])",
                "        index += 2",
                "    else:",
                "        index += 1",
                "if 'unknown' in servers:",
                "    print('ERROR: unknown runnable MCP server: unknown', file=sys.stderr)",
                "    raise SystemExit(2)",
                "if not servers or servers == ['none']:",
                "    print('-c')",
                "    print('mcp_servers={}')",
                "else:",
                "    for server in servers:",
                "        print('-c')",
                "        print(f'mcp_servers.{server}.url=\"mock://{server}\"')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return helper


def mock_result(returncode=0, stdout="output", stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def completion_output(summary: str = "baseline fixed") -> str:
    return "\n".join(
        [
            "검증 명령/결과: pytest => passed",
            "최종 산출물 경로: docs/exec-plans/active/2026-04-10-active.md",
            f"마지막 checkpoint 요약: {summary}",
            "<promise>HARNESS_COMPLETE</promise>",
        ]
    )


def closeout_variant_completion_output(summary: str = "variant closeout fixed") -> str:
    return "\n".join(
        [
            "검증 결과:",
            "- `pytest .agents/skills/harness/run-all-tests/tests/test_harness_loop.py -q` PASS",
            "최종 산출물: `.agents/skills/harness/core-engine/harness_loop.py`",
            f"마지막 checkpoint: {summary}",
            "<promise>HARNESS_COMPLETE</promise>",
        ]
    )


REAL_CODEX_PROCESS_SCRIPT = (
    "import subprocess, sys, time; "
    "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
    "sys.stdin.read(); "
    "time.sleep(30)"
)


def wait_for_process_group_exit(pgid: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def evolution_completion_output(summary: str = "evolution closeout") -> str:
    return "\n".join(
        [
            "검증 명령/결과: python3 -m pytest .agents/skills/harness/run-all-tests/tests/test_harness_loop.py -q => passed",
            "최종 산출물 경로: .agents/skills/harness-evolution/SKILL.md, .agents/skills/harness/core-engine/harness_loop.py",
            f"마지막 checkpoint 요약: {summary}",
            "strategy_artifact_path: .agents/skills/harness-evolution/SKILL.md",
            "final_conclusion_path: docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md#final-closeout-evidence",
            "harness-architect: PASS",
            "<promise>HARNESS_COMPLETE</promise>",
        ]
    )

def test_completes_on_promise(tmp_path):
    loop, sf = make_loop(tmp_path)
    with patch("cli_adapters.ClaudeAdapter.run",
               return_value=(0, completion_output("최종 요약입니다."))):
        assert loop.run() == 0
    assert sf.exists()
    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "completed"
    assert loaded.loop_id.startswith("loop-")
    assert "검증 명령/결과" in loaded.result_summary
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert [event["type"] for event in events] == [
        "loop_started",
        "iteration_started",
        "loop_completed",
    ]
    assert events[0]["loop_id"] == loaded.loop_id
    assert "검증 명령/결과" in events[-1]["result_summary"]


def test_completes_on_promise_with_closeout_label_variants(tmp_path):
    loop, sf = make_loop(tmp_path)
    with patch(
        "cli_adapters.ClaudeAdapter.run",
        return_value=(0, closeout_variant_completion_output("variant accepted")),
    ):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "completed"
    assert loaded.last_event == "loop_completed"


def test_completion_evidence_accepts_history_structured_fields():
    output = "\n".join(
        [
            "verification_result=`PASS readme-universal-final-contract`",
            "final_artifact=README.md",
            "last_checkpoint=`README universal Agent Harness iteration 3 completion 재검증 완료`",
        ]
    )
    assert has_completion_evidence(output)


def test_completion_evidence_rejects_bare_promise_without_evidence():
    assert not has_completion_evidence("<promise>HARNESS_COMPLETE</promise>")


def test_diagnostic_outcome_vocabulary():
    assert diagnostic_for_event("loop_completed") == (
        "completed",
        "none",
        "completion promise accepted with required evidence",
    )
    assert diagnostic_for_event("escalation_pending")[0:2] == ("blocked", "escalation_pending")
    assert diagnostic_for_event("completion_contract_missing")[0:2] == ("retrying", "completion_contract")
    assert diagnostic_for_event("timeout")[0:2] == ("retrying", "timeout")
    assert diagnostic_for_event("stagnation")[0:2] == ("retrying", "stagnation")
    assert diagnostic_for_event("loop_stopped", "max_iterations:1")[0:2] == ("stopped", "iteration_budget")


def test_terminal_events_include_outcome(tmp_path):
    loop, sf = make_loop(tmp_path)
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, completion_output())):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.outcome_code == "completed"
    assert loaded.failure_class == "none"
    assert "completion promise accepted" in loaded.status_hint
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    terminal = events[-1]
    assert terminal["type"] == "loop_completed"
    assert terminal["outcome_code"] == "completed"
    assert terminal["failure_class"] == "none"
    assert "status_hint" in terminal


def test_completion_branch_behavior_unchanged(tmp_path):
    loop, sf = make_loop(tmp_path)
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, completion_output("diagnostic only"))):
        assert loop.run() == 0
    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "completed"
    assert loaded.last_event == "loop_completed"
    assert loaded.outcome_code == "completed"


def test_extracts_plan_path_into_state_and_events(tmp_path):
    write_reviewed_active_plan(tmp_path, "docs/exec-plans/active/2026-04-10-sample.md")
    prompt = "docs/exec-plans/active/2026-04-10-sample.md 계획 문서를 기준으로 랄프 루프로 개발하라"
    loop, sf = make_loop(tmp_path, prompt=prompt)
    with patch("cli_adapters.ClaudeAdapter.run",
               return_value=(0, completion_output())):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.plan_path == "docs/exec-plans/active/2026-04-10-sample.md"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[0]["plan_path"] == "docs/exec-plans/active/2026-04-10-sample.md"
    assert events[1]["plan_path"] == "docs/exec-plans/active/2026-04-10-sample.md"
    assert events[-1]["plan_path"] == "docs/exec-plans/active/2026-04-10-sample.md"


def test_mcp_free_default_records_state_and_configures_codex(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex")
    captured = {}

    def fake_run(self, prompt, timeout=300):
        captured["mcp_config_args"] = self._mcp_config_args
        return 0, completion_output()

    with patch("cli_adapters.CodexAdapter.run", new=fake_run):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.mcp_servers == "[]"
    assert captured["mcp_config_args"] == ["-c", "mcp_servers={}"]
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[0]["mcp_servers"] == "[]"


def test_mcp_plan_selection_configures_codex_adapter(tmp_path):
    write_mcp_render_helper(tmp_path)
    plan_path = write_reviewed_active_plan(
        tmp_path,
        "docs/exec-plans/active/2026-04-10-mcp-selection.md",
        mcp_servers="[penpot, stitch]",
    )
    loop, sf = make_loop(
        tmp_path,
        cli="codex",
        prompt=f"{plan_path} 계획 문서를 기준으로 랄프 루프로 개발하라",
    )
    captured = {}

    def fake_run(self, prompt, timeout=300):
        captured["mcp_config_args"] = self._mcp_config_args
        return 0, completion_output()

    with patch("cli_adapters.CodexAdapter.run", new=fake_run):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.mcp_servers == '["penpot","stitch"]'
    rendered = "\n".join(captured["mcp_config_args"])
    assert "mcp_servers.penpot.url" in rendered
    assert "mcp_servers.stitch.url" in rendered
    assert "mcp_servers={}" not in rendered


def test_unknown_mcp_blocks_dispatch(tmp_path):
    write_mcp_render_helper(tmp_path)
    plan_path = write_reviewed_active_plan(
        tmp_path,
        "docs/exec-plans/active/2026-04-10-unknown-mcp.md",
        mcp_servers="[unknown]",
    )
    loop, sf = make_loop(
        tmp_path,
        cli="codex",
        prompt=f"{plan_path} 계획 문서를 기준으로 랄프 루프로 개발하라",
    )

    with patch("cli_adapters.CodexAdapter.run", side_effect=AssertionError("child must not dispatch")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "mcp_selection_error"
    assert loaded.stop_reason == "mcp_selection_error"
    assert "unknown runnable MCP server" in loaded.current_step
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "mcp_selection_error"


@pytest.mark.parametrize(
    ("mcp_servers", "expected"),
    [
        ('"penpot"', "mcp_servers must be a list of server names"),
        ('{"name":"penpot"}', "mcp_servers must be a list of server names"),
        ("[pen/pot]", "invalid MCP server name: pen/pot"),
        ('["none","penpot"]', "mcp_servers cannot combine none with server names"),
        ("[penpot", "mcp_servers must be a list"),
    ],
)
def test_malformed_mcp_servers_blocks_dispatch_before_child_launch(tmp_path, mcp_servers, expected):
    plan_path = write_reviewed_active_plan(
        tmp_path,
        "docs/exec-plans/active/2026-04-10-malformed-mcp.md",
        mcp_servers=mcp_servers,
    )
    loop, sf = make_loop(
        tmp_path,
        cli="codex",
        prompt=f"{plan_path} 계획 문서를 기준으로 랄프 루프로 개발하라",
    )

    with patch("cli_adapters.CodexAdapter.run", side_effect=AssertionError("child must not dispatch")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "mcp_selection_error"
    assert loaded.stop_reason == "mcp_selection_error"
    assert expected in loaded.current_step


def test_harness_evolution_context_detection():
    assert is_harness_evolution_context(
        "docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md 계획을 실행하라",
        "docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md",
    )
    assert is_harness_evolution_context("run harness-evolution skill", "")
    assert not is_harness_evolution_context("docs/exec-plans/active/2026-04-10-active.md 계획을 실행하라", "")


def test_harness_evolution_completion_evidence_detection():
    assert has_evolution_completion_evidence(evolution_completion_output())
    assert not has_evolution_completion_evidence(completion_output())


def test_harness_evolution_requires_extra_completion_evidence(tmp_path):
    plan_path = write_reviewed_active_plan(
        tmp_path, "docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md"
    )
    loop, sf = make_loop(
        tmp_path,
        prompt=f"{plan_path} 계획을 실행하고 harness-evolution 결과를 닫아라",
        max_iterations=1,
        iteration=1,
    )

    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, completion_output("missing evolution evidence"))):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:1"
    assert loaded.last_event == "completion_contract_missing"
    assert "strategy_artifact_path" in loaded.current_step
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "loop_stopped"
    assert any(event["type"] == "completion_contract_missing" for event in events)


def test_stops_on_completion_contract_missing(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, "<promise>HARNESS_COMPLETE</promise>")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "completion_contract_missing"
    assert loaded.stop_reason == "max_iterations:1"
    assert loaded.outcome_code == "stopped"
    assert loaded.failure_class == "iteration_budget"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    missing = next(event for event in events if event["type"] == "completion_contract_missing")
    assert missing["outcome_code"] == "retrying"
    assert missing["failure_class"] == "completion_contract"


def test_harness_evolution_completes_with_extra_completion_evidence(tmp_path):
    plan_path = write_reviewed_active_plan(
        tmp_path, "docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md"
    )
    loop, sf = make_loop(
        tmp_path,
        prompt=f"{plan_path} 계획을 실행하고 harness-evolution 결과를 닫아라",
        max_iterations=1,
        iteration=1,
    )

    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, evolution_completion_output())):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "completed"
    assert loaded.last_event == "loop_completed"

def test_stops_on_max_iterations(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=2, iteration=3)
    assert loop.run() == 1
    assert sf.exists()  # 비정상 종료 시 파일 유지
    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "max_iterations:2"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "loop_stopped"


def test_iteration_budget(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=2, iteration=3)
    assert loop.run() == 1
    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:2"
    assert loaded.outcome_code == "stopped"
    assert loaded.failure_class == "iteration_budget"

def test_stops_on_cd_limit(tmp_path):
    loop, sf = make_loop(tmp_path)
    loop.history_file.write_text("\n".join(["[ESCALATION]"] * 30))
    assert loop.run() == 1

def test_stops_on_cli_not_found(tmp_path):
    loop, sf = make_loop(tmp_path)
    with patch("cli_adapters.ClaudeAdapter.run", side_effect=FileNotFoundError()):
        assert loop.run() == 1

def test_dry_run_no_cli_call(tmp_path):
    """--dry-run: loop-state.md 생성 후 CLI 호출 없이 종료"""
    state_file = tmp_path / ".agents" / "traces" / "harness" / "loop-state.md"
    history_file = tmp_path / "HISTORY.md"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("")

    with patch.object(sys, "argv", ["harness_loop.py", "--dry-run", "test prompt", "--cli", "claude"]), \
         patch("harness_loop.subprocess.check_output", return_value=str(tmp_path)), \
         patch("builtins.print") as print_mock:
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0

    assert state_file.exists()
    loaded = LoopState.from_file(state_file)
    assert loaded.active is False
    assert loaded.stop_reason == "dry_run"
    printed = "\n".join(" ".join(str(arg) for arg in call.args) for call in print_mock.call_args_list)
    assert "[DRY-RUN]" in printed


def test_shell_dry_run_marks_state_inactive(tmp_path):
    script = Path(__file__).parent.parent.parent.absolute() / "core-engine" / "scripts" / "harness-loop.sh"
    state_file = tmp_path / ".agents" / "traces" / "harness" / "loop-state.md"

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = subprocess.run(
        ["bash", str(script), "--dry-run", "test prompt", "--cli", "claude"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "[DRY-RUN]" in result.stdout
    assert state_file.exists()
    loaded = LoopState.from_file(state_file)
    assert loaded.active is False


def test_shell_codex_invocation_uses_danger_full_access_contract(tmp_path):
    script = Path(__file__).parent.parent.parent.absolute() / "core-engine" / "scripts" / "harness-loop.sh"
    repo_root = Path(__file__).resolve().parents[5]
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    capture_file = tmp_path / "codex-argv.txt"
    state_file = tmp_path / ".agents" / "traces" / "harness" / "loop-state.md"
    events_file = tmp_path / ".agents" / "traces" / "harness" / "events.jsonl"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    shim_path = shim_dir / "codex"
    shim_path.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$@\" > \"$HARNESS_TEST_CAPTURE\"\n"
        "cat >/dev/null\n"
        "printf '검증 명령/결과: shim => passed\\n최종 산출물 경로: shim\\n마지막 checkpoint 요약: shim closeout\\n<promise>HARNESS_COMPLETE</promise>\\n'\n",
        encoding="utf-8",
    )
    shim_path.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{shim_dir}:{env['PATH']}"
    env["HARNESS_TEST_CAPTURE"] = str(capture_file)
    env["HARNESS_LOOP_STATE_FILE"] = str(state_file)
    env["HARNESS_LOOP_EVENTS_FILE"] = str(events_file)

    result = subprocess.run(
        ["bash", str(script), "test prompt", "--cli", "codex", "--max-iterations", "1", "--yes"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    assert "<promise>HARNESS_COMPLETE</promise>" in result.stdout
    argv = capture_file.read_text(encoding="utf-8").splitlines()
    assert argv == [
        "exec",
        "-s",
        "danger-full-access",
        "-c",
        'approval_policy="never"',
        "-",
    ]


def test_main_yes_skips_confirmation(tmp_path):
    state_file = tmp_path / ".agents" / "traces" / "harness" / "loop-state.md"
    history_file = tmp_path / "HISTORY.md"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("")

    with patch.object(sys, "argv", ["harness_loop.py", "--yes", "test prompt", "--cli", "claude"]), \
         patch("harness_loop.subprocess.check_output", return_value=str(tmp_path)), \
         patch("harness_loop.confirm_cli_execution", side_effect=AssertionError("should not prompt")), \
         patch("harness_loop.HarnessLoop.run", return_value=0):
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0

    assert state_file.exists()
    loaded = LoopState.from_file(state_file)
    assert loaded.active is True
    assert loaded.cli == "claude"


def test_read_history_delta_tolerates_mid_utf8_offset(tmp_path):
    loop, _ = make_loop(tmp_path)
    text = "[2026-05-05T10:51:01Z] [CHECKPOINT] 하네스 검증 완료\n"
    encoded = text.encode("utf-8")
    loop.history_file.write_bytes(encoded)
    offset = encoded.index("하".encode("utf-8")) + 1
    lines, new_offset = loop._read_history_delta(offset)
    assert new_offset == len(encoded)
    assert lines


def test_trigger4_warning(tmp_path):
    """HISTORY.md 500줄 도달 시 TRIGGER 4 경고 출력"""
    loop, sf = make_loop(tmp_path)
    loop.history_file.write_text("\n" * 500)
    with patch("cli_adapters.ClaudeAdapter.run",
               return_value=(0, completion_output())):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            loop.run()
        output = buf.getvalue()
        assert "TRIGGER 4" in output
        assert "compact_history.py" in output
        assert "--keep-recent-lines 200" in output


def test_history_compaction_guidance_tokens():
    command_doc = (
        Path(__file__).resolve().parents[2] / "core-engine" / "commands" / "harness-loop.md"
    ).read_text(encoding="utf-8")
    script = (
        Path(__file__).resolve().parents[2] / "core-engine" / "scripts" / "harness-loop.sh"
    ).read_text(encoding="utf-8")
    utility = (
        Path(__file__).resolve().parents[2] / "core-engine" / "scripts" / "compact_history.py"
    ).read_text(encoding="utf-8")
    for text in (command_doc, script):
        assert "compact_history.py" in text
        assert "2026-04-history-archive.md" in text
        assert "--keep-recent-lines 200" in text
    assert "KEEP_RECENT_LINES = 200" in utility
    assert "archive_path" in utility
    assert "HISTORY.md" in utility

def test_heartbeat_output(tmp_path):
    """5번째 이터레이션에서 HEARTBEAT 출력"""
    loop, sf = make_loop(tmp_path, iteration=5)
    with patch("cli_adapters.ClaudeAdapter.run",
               return_value=(0, completion_output())):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            loop.run()
        assert "HEARTBEAT" in buf.getvalue()


def test_progress_heartbeat_updates_state_and_events_before_child_exit(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    loop.child_progress_poll_seconds = 0.01
    loop.child_progress_heartbeat_seconds = 0.02
    result: dict[str, int] = {}

    def slow_run(prompt, timeout=300):
        time.sleep(0.06)
        return 0, completion_output("progress heartbeat closeout")

    def run_loop():
        result["code"] = loop.run()

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=slow_run):
        worker = threading.Thread(target=run_loop)
        worker.start()
        seen_heartbeat = False
        deadline = time.time() + 1
        while time.time() < deadline:
            loaded = LoopState.from_file(sf)
            if loaded.last_event == "progress_heartbeat":
                seen_heartbeat = True
                assert loaded.current_task == "Running child CLI"
                assert "Heartbeat:" in loaded.current_step
                break
            time.sleep(0.01)
        worker.join(timeout=1)

    assert seen_heartbeat is True


def test_escalation_summary_bound(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    oversized = "A" * 400
    output = "\n".join(
        [
            f"[ESCALATION] {oversized}",
            "follow-up line that should not be copied wholesale",
        ]
    )
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, output)):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    escalation_event = next(event for event in events if event["type"] == "escalation_requested")
    assert len(escalation_event["summary"]) <= 240
    assert escalation_event["summary"].startswith("A")
    assert escalation_event["summary"].endswith("...")


def test_events_rotation(tmp_path):
    loop, _ = make_loop(tmp_path)
    loop.events_max_bytes = 150
    loop.events_max_archives = 2

    for idx in range(6):
        loop._append_event("checkpoint_detected", idx + 1, f"summary-{idx}", loop_id=f"loop-{idx}")

    active = events_path(tmp_path)
    archives = sorted(active.parent.glob("events.*.jsonl.gz"))
    assert active.exists()
    assert active.stat().st_size > 0
    assert len(archives) == 2
    with gzip.open(archives[-1], "rt", encoding="utf-8") as fh:
        archived_lines = [json.loads(line) for line in fh if line.strip()]
    assert archived_lines
    assert all(event["type"] == "checkpoint_detected" for event in archived_lines)


def test_completed_state_cleanup_clears_stale_escalation(tmp_path):
    loop, sf = make_loop(
        tmp_path,
        pending_escalation_id="esc-001",
        pending_escalation_summary="need direction",
        pending_override_response="override",
    )
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, completion_output("cleanup"))):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    assert loaded.pending_override_response == ""


def test_closeout_clears_stale_escalation_on_max_iterations(tmp_path):
    loop, sf = make_loop(
        tmp_path,
        pending_escalation_id="esc-001",
        pending_escalation_summary="need direction",
        pending_override_response="override",
        max_iterations=1,
        iteration=2,
    )
    assert loop.run() == 1
    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    assert loaded.pending_override_response == ""


def test_history_checkpoint_reflection_updates_state_before_child_exit(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    loop.child_progress_poll_seconds = 0.01
    loop.child_progress_heartbeat_seconds = 0.05
    result: dict[str, int] = {}

    def slow_run(prompt, timeout=300):
        time.sleep(0.02)
        loop.history_file.write_text(
            '[2026-04-11T00:00:00Z] [CHECKPOINT] Iteration 2 progress | heartbeat reflected\n',
            encoding="utf-8",
        )
        time.sleep(0.04)
        return 0, completion_output("checkpoint reflection closeout")

    def run_loop():
        result["code"] = loop.run()

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=slow_run):
        worker = threading.Thread(target=run_loop)
        worker.start()
        seen_checkpoint = False
        deadline = time.time() + 1
        while time.time() < deadline:
            loaded = LoopState.from_file(sf)
            if loaded.last_event == "checkpoint":
                seen_checkpoint = True
                assert loaded.current_phase == "Iteration 2 progress"
                assert loaded.current_task == "heartbeat reflected"
                break
            time.sleep(0.01)
        worker.join(timeout=1)

    assert seen_checkpoint is True
    assert result["code"] == 0
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "checkpoint_detected" for event in events)


def test_incremental_history_poll_avoids_full_reread(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    loop.child_progress_poll_seconds = 0.01
    loop.child_progress_heartbeat_seconds = 0.05
    original_read = loop._read_history_lines
    read_calls = {"count": 0}

    def guarded_read():
        read_calls["count"] += 1
        if read_calls["count"] > 1:
            raise AssertionError("full history reread should not happen during child polling")
        return original_read()

    def slow_run(prompt, timeout=300):
        time.sleep(0.02)
        loop.history_file.write_text(
            '[2026-04-11T00:00:00Z] [CHECKPOINT] Incremental poll | delta only\n',
            encoding="utf-8",
        )
        time.sleep(0.02)
        return 0, completion_output("incremental history closeout")

    with patch.object(loop, "_read_history_lines", side_effect=guarded_read), \
         patch("cli_adapters.ClaudeAdapter.run", side_effect=slow_run):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    checkpoint_event = next(event for event in events if event["type"] == "checkpoint_detected")
    assert checkpoint_event["phase"] == "Incremental poll"
    assert checkpoint_event["task"] == "delta only"
    assert read_calls["count"] == 1


def test_progress_heartbeat_does_not_count_as_stagnation(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    loop.child_progress_poll_seconds = 0.01
    loop.child_progress_heartbeat_seconds = 0.02

    def slow_run(prompt, timeout=300):
        time.sleep(0.06)
        return 0, "still working"

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=slow_run):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:1"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "progress_heartbeat" for event in events)
    assert all(event["type"] != "stagnation" for event in events)


def test_blocked_output_updates_state_and_events(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)

    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, "[ESCALATION] need help")):
        assert loop.run() == 1

    assert sf.exists()
    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "max_iterations:1"
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    escalation_event = next(event for event in events if event["type"] == "escalation_requested")
    assert escalation_event["request_id"] == "esc-001"
    assert escalation_event["summary"] == "need help"


def test_escalation_pending(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, "[ESCALATION] need operator audit")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:1"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    escalation = next(event for event in events if event["type"] == "escalation_requested")
    assert escalation["outcome_code"] == "blocked"
    assert escalation["failure_class"] == "escalation_pending"


def test_load_default_cli_from_root_config(tmp_path):
    config = tmp_path / ".harness-loop.json"
    config.write_text('{"default_cli": "codex"}\n')
    assert load_default_cli(tmp_path) == "codex"


def test_load_default_cli_ignores_invalid_value(tmp_path):
    config = tmp_path / ".harness-loop.json"
    config.write_text('{"default_cli": "invalid"}\n')
    assert load_default_cli(tmp_path) is None


def test_confirm_cli_execution_accepts_yes():
    assert confirm_cli_execution("codex", input_fn=lambda _: "y") is True


def test_confirm_cli_execution_rejects_default():
    assert confirm_cli_execution("claude", input_fn=lambda _: "") is False


def test_ralph_plan_goal_artifact_contract_is_documented():
    repo_root = Path(__file__).resolve().parents[5]
    reviewer = (repo_root / ".agents" / "agents" / "harness" / "plan-reviewer.md").read_text(encoding="utf-8")
    writing_plans = (repo_root / ".agents" / "skills" / "harness" / "writing-plans" / "SKILL.md").read_text(encoding="utf-8")

    for token in [
        "사용자 목적이 Goal 또는 동등 섹션에 한 문장으로 재진술",
        "최종 산출물 경로와 파일 책임",
        "최종 결론 저장 위치가 intermediate checkpoint 위치와 구분",
    ]:
        assert token in reviewer

    for token in [
        "사용자 목적이 한 문장 Goal로 재진술됐는가?",
        "최종 산출물이 어떤 파일/경로에 저장되는가?",
        "최종 결론 저장 위치가 intermediate checkpoint 위치와 구분",
        "Goal, 최종 산출물, 최종 결론 저장 위치 중 하나라도 빠지면 loop mode 계획은 Gate 1 FAIL",
    ]:
        assert token in writing_plans


def test_iteration_budget_contract_is_documented():
    repo_root = Path(__file__).resolve().parents[5]
    command_doc = (repo_root / ".agents" / "skills" / "harness" / "core-engine" / "commands" / "harness-loop.md").read_text(encoding="utf-8")
    for token in [
        "Iteration Budget Gate",
        "LoopState.max_iterations",
        "iteration == max_iterations",
        "iteration > max_iterations",
    ]:
        assert token in command_doc


# ── fresh-process / context reset 계약 테스트 ──────────────────────────────

def test_claude_adapter_creates_new_process_per_run():
    """ClaudeAdapter.run()은 매 호출마다 새 Popen 프로세스를 생성한다.
    [계약] 장기 세션 재사용 없음 — subprocess.Popen이 호출당 1회씩 생성.
    """
    import subprocess
    from cli_adapters import ClaudeAdapter

    adapter = ClaudeAdapter()
    call_count = 0

    original_popen = subprocess.Popen

    def counting_popen(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        # 실제 프로세스를 생성하지 않고 Mock으로 대체
        from unittest.mock import MagicMock
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["<promise>HARNESS_COMPLETE</promise>\n"])
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        return mock_proc

    with patch("cli_adapters.subprocess.Popen", side_effect=counting_popen):
        adapter.run("test prompt")
        adapter.run("test prompt")

    # 2번 호출 → Popen이 2번 생성 (세션 재사용 없음)
    assert call_count == 2, f"Expected 2 new processes, got {call_count}"


def test_codex_adapter_creates_new_process_per_run():
    """CodexAdapter.run()은 매 호출마다 subprocess.Popen으로 새 프로세스를 생성한다.
    [계약] 이전 호출의 상태를 재사용하지 않는다.
    """
    from cli_adapters import CodexAdapter

    adapter = CodexAdapter()
    call_count = 0

    def counting_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "usage: codex exec --output-last-message <file>\n"
        result.stderr = ""
        return result

    def counting_popen(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.returncode = 0
        proc.communicate = MagicMock(return_value=("<promise>HARNESS_COMPLETE</promise>", ""))
        proc.kill = MagicMock()
        return proc

    with patch.object(CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch("cli_adapters.subprocess.run", side_effect=counting_run), \
         patch("cli_adapters.subprocess.Popen", side_effect=counting_popen):
        adapter.run("prompt A")
        adapter.run("prompt B")

    assert call_count == 2, f"Expected 2 new processes, got {call_count}"


def test_codex_prompt_echo_does_not_trigger_false_completion(tmp_path):
    plan_path = write_reviewed_active_plan(tmp_path)
    loop, sf = make_loop(
        tmp_path,
        cli="codex",
        prompt=f"{plan_path} verify prompt echo handling with <promise>HARNESS_COMPLETE</promise>",
        max_iterations=1,
        iteration=1,
    )
    echoed_stdout = "[PROMPT_ECHO] <promise>HARNESS_COMPLETE</promise>"
    expected_last_message = "codex final response without prompt echo"

    def codex_run_side_effect(cmd, **kwargs):
        if "--help" in cmd:
            return mock_result(stdout="usage: codex exec --output-last-message <file>\n")
        raise AssertionError(f"Unexpected command: {cmd}")

    def codex_popen_side_effect(cmd, **kwargs):
        if "--output-last-message" in cmd:
            output_path = Path(cmd[cmd.index("--output-last-message") + 1])
            output_path.write_text(expected_last_message, encoding="utf-8")
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.returncode = 0
        proc.communicate = MagicMock(return_value=(echoed_stdout, ""))
        proc.kill = MagicMock()
        return proc

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with patch("cli_adapters.subprocess.run", side_effect=codex_run_side_effect), \
         patch("cli_adapters.subprocess.Popen", side_effect=codex_popen_side_effect), \
         redirect_stdout(buf):
        assert loop.run() == 1

    printed = buf.getvalue()
    assert echoed_stdout not in printed
    assert expected_last_message in printed

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "max_iterations:1"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert all(event["type"] != "loop_completed" for event in events)


def test_stagnation_updates_state_and_events(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex", max_iterations=1, iteration=1)

    with patch("cli_adapters.CodexAdapter.run", return_value=(-2, "[STAGNATION] Codex child made no progress for 60s | last_message_size=0")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "max_iterations:1"
    assert loaded.result_summary.startswith("[STAGNATION]")
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "stagnation" for event in events)
    assert all(event["type"] != "loop_completed" for event in events)


def test_stagnation_timeout_option_configures_codex_adapter(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex")
    loop.stagnation_timeout = 180.0
    adapter = MagicMock()
    adapter.run.return_value = (0, completion_output("configured stagnation timeout"))

    with patch("harness_loop.CLIAdapter.get", return_value=adapter):
        assert loop.run() == 0

    adapter.configure_stagnation_timeout.assert_called_once_with(180.0)
    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "completed"


def test_stagnation_with_prompt_promise_does_not_enter_completion_contract(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex", max_iterations=1, iteration=1)
    output = "\n".join(
        [
            "[STAGNATION] Codex child made no progress for 60s | last_message_size=0",
            "[cleanup] process_group_terminated",
            "[output_last_message] fallback_reason=empty_file",
            "prompt echo <promise>HARNESS_COMPLETE</promise>",
        ]
    )

    with patch("cli_adapters.CodexAdapter.run", return_value=(-2, output)):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "stagnation"
    assert loaded.stop_reason == "max_iterations:1"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    event_types = [event["type"] for event in events]
    assert "stagnation" in event_types
    assert "loop_completed" not in event_types
    assert "completion_contract_missing" not in event_types


def test_events_log_written_for_checkpoint(tmp_path):
    loop, sf = make_loop(tmp_path)

    def write_checkpoint(prompt, timeout=300):
        loop.history_file.write_text(
            '[2026-04-09T00:00:00Z] [CHECKPOINT] Phase 0-1 완료 | baseline fixed\n'
        )
        time.sleep(0.02)
        return 0, completion_output()

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=write_checkpoint):
        assert loop.run() == 0

    events = events_path(tmp_path).read_text()
    assert "loop_started" in events
    assert "checkpoint_detected" in events
    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "loop_completed"
    assert loaded.last_checkpoint_at != "null"
    assert loaded.current_phase == "Phase 0-1 완료"


def test_no_iteration_artifact_created_on_completion(tmp_path):
    loop, sf = make_loop(tmp_path)
    trace_dir = tmp_path / ".agents" / "traces" / "harness"

    with patch("cli_adapters.ClaudeAdapter.run",
               return_value=(0, completion_output())):
        assert loop.run() == 0

    assert sf.exists()
    assert list(trace_dir.glob("iter-*.txt")) == []


def test_state_records_blocked_reason_from_history(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)

    def write_escalation(prompt, timeout=300):
        loop.history_file.write_text(
            '[2026-04-09T00:00:00Z] [ESCALATION] tmux access denied\n'
        )
        time.sleep(0.02)
        return 0, "need input"

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=write_escalation):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""
    assert loaded.pending_escalation_summary == ""
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    escalation_event = next(event for event in events if event["type"] == "escalation_requested")
    assert escalation_event["request_id"] == "esc-001"
    assert escalation_event["summary"] == "tmux access denied"


def test_default_progress_continues_without_response(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=2, iteration=1)
    outputs = [
        (0, "[ESCALATION] need direction"),
        (0, "still working"),
    ]

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=outputs):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.stop_reason == "max_iterations:2"
    assert loaded.pending_escalation_id == ""
    assert loaded.current_task == "Running child CLI"

    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert [event["type"] for event in events].count("iteration_started") == 2
    escalation_event = next(event for event in events if event["type"] == "escalation_requested")
    assert escalation_event["request_id"] == "esc-001"
    assert escalation_event["summary"] == "need direction"


def test_override_sets_last_event_and_applies_once(tmp_path):
    loop, sf = make_loop(
        tmp_path,
        max_iterations=2,
        iteration=1,
        pending_escalation_id="esc-001",
        pending_escalation_summary="need direction",
        pending_override_response="switch direction",
    )
    prompts = []

    def run_side_effect(prompt, timeout=300):
        prompts.append(prompt)
        return (0, "still working")

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=run_side_effect):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:2"
    assert loaded.pending_override_response == ""
    assert loaded.pending_escalation_id == ""
    assert loaded.last_event == "loop_stopped"
    assert "[ESCALATION_RESPONSE] switch direction" in prompts[0]
    assert all("[ESCALATION_RESPONSE]" not in prompt for prompt in prompts[1:])

    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "escalation_resolved" for event in events)


def test_stale_override_is_ignored(tmp_path):
    loop, sf = make_loop(
        tmp_path,
        max_iterations=1,
        iteration=1,
        pending_override_response="stale response",
    )
    prompts = []

    def run_side_effect(prompt, timeout=300):
        prompts.append(prompt)
        return (0, "still working")

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=run_side_effect):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.pending_override_response == ""
    assert "[ESCALATION_RESPONSE]" not in prompts[0]
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "escalation_override_ignored" for event in events)


def test_state_keeps_stop_reason_on_limit(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=2)
    assert loop.run() == 1
    loaded = LoopState.from_file(sf)
    assert loaded.stop_reason == "max_iterations:1"


def test_iteration_budget_allows_closeout_but_blocks_next_dispatch(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)
    calls = {"count": 0}

    def run_side_effect(prompt, timeout=300):
        calls["count"] += 1
        return 0, "still working"

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=run_side_effect):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert calls["count"] == 1
    assert loaded.stop_reason == "max_iterations:1"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert [event["type"] for event in events].count("iteration_started") == 1


def test_planning_redirect_requires_reviewed_plan_or_execution_contract(tmp_path):
    loop, sf = make_loop(tmp_path, prompt="버그를 고쳐라", max_iterations=1, iteration=1)

    assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "planning_redirect"
    assert loaded.stop_reason == "planning_required"
    assert "writing-plans" in loaded.current_task
    assert "prd.json/progress.txt" in loaded.current_step
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "planning_redirect"


def test_execution_contract_normalizes_to_active_plan_and_refreshes_registry(tmp_path):
    prompt = "\n".join(
        [
            "[EXECUTION_CONTRACT]",
            "Goal: Harden the loop gate",
            "Scope: .agents/skills/harness/core-engine/harness_loop.py",
            "Actions: Add deterministic normalization gate",
            "Verification: python3 -m pytest .agents/skills/harness/run-all-tests/tests/test_harness_loop.py -q",
            "Done When: reviewed active plan exists and review gate is required",
            "[/EXECUTION_CONTRACT]",
        ]
    )
    loop, sf = make_loop(tmp_path, prompt=prompt, max_iterations=1, iteration=1)

    assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.active is False
    assert loaded.last_event == "plan_normalized"
    assert loaded.stop_reason == "review_required"
    assert loaded.plan_path.startswith("docs/exec-plans/active/")
    normalized_plan = (tmp_path / loaded.plan_path)
    assert normalized_plan.exists()
    plan_text = normalized_plan.read_text(encoding="utf-8")
    assert "> **상태:** 구현 계획 (리뷰 대기)<br>" in plan_text
    assert "> mcp_servers: []" in plan_text
    assert "**사용자 결과:**" in plan_text
    assert "## 사용자 결과 요약" in plan_text
    assert "## 사용자 진행 계획" in plan_text
    assert "## MCP 사용 계획" in plan_text
    assert "Expected Evidence: child launch renders `mcp_servers={}`" in plan_text
    assert "[EXECUTION_CONTRACT]" in plan_text
    assert "## 정규화된 실행 계약" in plan_text
    plan_json = json.loads((tmp_path / ".agents" / "mission" / "plan.json").read_text(encoding="utf-8"))
    assert any(item["path"] == loaded.plan_path for item in plan_json["active_plans"])
    readme = (tmp_path / "docs" / "exec-plans" / "README.md").read_text(encoding="utf-8")
    assert loaded.plan_path in readme


def test_completion_after_quiet_prefers_completion_over_stagnation(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex", max_iterations=1, iteration=1)
    output = "\n".join(
        [
            "[completion-after-quiet] completion-after-quiet promise detected before stagnation closeout",
            "검증 명령/결과: pytest => passed",
            "최종 산출물 경로: docs/exec-plans/active/2026-04-10-active.md",
            "마지막 checkpoint 요약: quiet closeout",
            "<promise>HARNESS_COMPLETE</promise>",
        ]
    )

    with patch("cli_adapters.CodexAdapter.run", return_value=(0, output)):
        assert loop.run() == 0

    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "loop_completed"
    assert loaded.stop_reason == "completed"
    assert "completion-after-quiet" in loaded.result_summary


def test_completion_requires_evidence_contract(tmp_path):
    loop, sf = make_loop(tmp_path)

    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, "<promise>HARNESS_COMPLETE</promise>")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "completion_contract_missing"
    assert "bare promise rejected" in loaded.current_step


def test_launch_failure_surfaces_specific_event_phase(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex", max_iterations=1, iteration=1)

    with patch("cli_adapters.CodexAdapter.run", return_value=(125, "[launch] launch failure: spawn exploded\n[trace] /tmp/codex-trace.log")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "launch_failure"
    assert loaded.current_step == "launch failure"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert any(event["type"] == "launch_failure" for event in events)


def test_dispatch_failure_surfaces_specific_event_phase(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex", max_iterations=1, iteration=1)

    with patch("cli_adapters.CodexAdapter.run", return_value=(124, "[dispatch] dispatch failure: stdin closed\n[trace] /tmp/codex-trace.log")):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "dispatch_failure"
    assert loaded.current_step == "dispatch failure"


def test_quoted_escalation_string_does_not_trigger_pending_escalation(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)

    with patch("cli_adapters.ClaudeAdapter.run", return_value=(0, 'log snippet says "[ESCALATION] keep going"')):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""


def test_history_checkpoint_with_quoted_escalation_does_not_trigger_pending_escalation(tmp_path):
    loop, sf = make_loop(tmp_path, max_iterations=1, iteration=1)

    def write_history(prompt, timeout=300):
        loop.history_file.write_text(
            '[2026-04-09T00:00:00Z] [CHECKPOINT] copied text "[ESCALATION] keep going" | baseline fixed\n'
        )
        return 0, "still working"

    with patch("cli_adapters.ClaudeAdapter.run", side_effect=write_history):
        assert loop.run() == 1

    loaded = LoopState.from_file(sf)
    assert loaded.pending_escalation_id == ""


def test_harness_loop_interrupt_cleans_active_child(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex")
    real_popen = subprocess.Popen
    spawned: dict[str, object] = {}

    def popen_wrapper(cmd, **kwargs):
        proc = real_popen(cmd, **kwargs)
        spawned["pgid"] = os.getpgid(proc.pid)
        return proc

    def send_sigint_when_ready() -> None:
        while "pgid" not in spawned:
            time.sleep(0.02)
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGINT)

    sender = threading.Thread(target=send_sigint_when_ready, daemon=True)
    sender.start()

    with patch.object(sys, "argv", ["harness_loop.py"]), \
         patch.object(__import__("cli_adapters").CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch.object(__import__("cli_adapters").CodexAdapter, "_build_launch_contract", return_value=[sys.executable, "-c", REAL_CODEX_PROCESS_SCRIPT]), \
         patch("cli_adapters.subprocess.Popen", side_effect=popen_wrapper), \
         pytest.raises(KeyboardInterrupt):
        loop.run()

    sender.join(timeout=1)
    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "loop_stopped"
    assert loaded.stop_reason == "interrupted"
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "loop_stopped"
    assert wait_for_process_group_exit(spawned["pgid"])


def test_harness_loop_signal_stop_cleans_active_child(tmp_path):
    loop, sf = make_loop(tmp_path, cli="codex")
    real_popen = subprocess.Popen
    spawned: dict[str, object] = {}

    def popen_wrapper(cmd, **kwargs):
        proc = real_popen(cmd, **kwargs)
        spawned["pgid"] = os.getpgid(proc.pid)
        return proc

    def send_sigterm_when_ready() -> None:
        while "pgid" not in spawned:
            time.sleep(0.02)
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGTERM)

    sender = threading.Thread(target=send_sigterm_when_ready, daemon=True)
    sender.start()

    with patch.object(__import__("cli_adapters").CodexAdapter, "_supports_output_last_message", return_value=False), \
         patch.object(__import__("cli_adapters").CodexAdapter, "_build_launch_contract", return_value=[sys.executable, "-c", REAL_CODEX_PROCESS_SCRIPT]), \
         patch("cli_adapters.subprocess.Popen", side_effect=popen_wrapper), \
         pytest.raises(SystemExit) as exc_info:
        loop.run()

    sender.join(timeout=1)
    loaded = LoopState.from_file(sf)
    assert loaded.last_event == "loop_stopped"
    assert loaded.stop_reason == "signal:SIGTERM"
    assert exc_info.value.code == 128 + signal.SIGTERM
    events = [json.loads(line) for line in events_path(tmp_path).read_text().splitlines()]
    assert events[-1]["type"] == "loop_stopped"
    assert wait_for_process_group_exit(spawned["pgid"])
