import json
import os
import signal
import sys
import time
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute() / "core-engine"))

from cli_adapters import CodexAdapter
from harness_loop import HarnessLoop
from loop_state import LoopState


def write_reviewed_active_plan(
    root: Path,
    relative_path: str = ".agentos/project/exec-plans/active/2026-04-30-mcp-lifecycle.md",
    mcp_servers: str = "[lifecycle-probe]",
) -> str:
    plan_path = root / relative_path
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "# MCP Lifecycle Probe Plan",
                "",
                "> **상태:** 구현 계획 (실행 대기)",
                "> **작성일:** 2026-04-30",
                "> reviewed: true",
                f"> mcp_servers: {mcp_servers}",
                "",
                "## MCP Usage Plan",
                "",
                "- Required MCPs: lifecycle-probe",
                "- Purpose: local lifecycle regression probe",
                "- When Used: test only",
                "- Preflight: local fake process only",
                "- Expected Evidence: marker files and events.jsonl mcp_servers evidence",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return relative_path


def make_loop(root: Path, plan_path: str, cli_timeout: int = 5) -> tuple[HarnessLoop, Path]:
    state_file = root / ".agents" / "traces" / "harness" / "loop-state.md"
    history_file = root / "HISTORY.md"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("", encoding="utf-8")
    LoopState(
        cli="codex",
        prompt=f"{plan_path} 계획 문서를 기준으로 랄프 루프로 개발하라",
        max_iterations=1,
    ).to_file(state_file)
    return HarnessLoop(state_file=state_file, history_file=history_file, cli_timeout=cli_timeout), state_file


def events(root: Path) -> list[dict[str, object]]:
    events_file = root / ".agents" / "traces" / "harness" / "events.jsonl"
    return [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines()]


def write_fake_mcp(root: Path) -> Path:
    script = root / "fake-mcp.py"
    script.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "import os",
                "import signal",
                "import sys",
                "import time",
                "",
                "marker = Path(sys.argv[1])",
                "marker.mkdir(parents=True, exist_ok=True)",
                "(marker / 'pid').write_text(str(os.getpid()), encoding='utf-8')",
                "(marker / 'started').write_text('started', encoding='utf-8')",
                "",
                "def stop(signum, frame):",
                "    (marker / 'stopped').write_text(signal.Signals(signum).name, encoding='utf-8')",
                "    raise SystemExit(0)",
                "",
                "signal.signal(signal.SIGTERM, stop)",
                "signal.signal(signal.SIGINT, stop)",
                "while True:",
                "    time.sleep(0.1)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return script


def lifecycle_mcp_args(fake_mcp: Path, marker_dir: Path) -> list[str]:
    return [
        "-c",
        f"mcp_servers.lifecycle-probe.command={json.dumps(sys.executable)}",
        "-c",
        "mcp_servers.lifecycle-probe.args="
        + json.dumps([str(fake_mcp), str(marker_dir)], separators=(",", ":")),
    ]


def write_lifecycle_mcp_render_helper(root: Path, fake_mcp: Path, marker_dir: Path) -> Path:
    helper = root / ".agents" / "mcp" / "scripts" / "render-codex-mcp-config.py"
    helper.parent.mkdir(parents=True, exist_ok=True)
    args_literal = json.dumps(lifecycle_mcp_args(fake_mcp, marker_dir))
    helper.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "",
                f"LIFECYCLE_ARGS = {args_literal!r}",
                "servers = []",
                "argv = sys.argv[1:]",
                "index = 0",
                "while index < len(argv):",
                "    if argv[index] == '--server':",
                "        servers.append(argv[index + 1])",
                "        index += 2",
                "    else:",
                "        index += 1",
                "if not servers or servers == ['none']:",
                "    print('-c')",
                "    print('mcp_servers={}')",
                "elif servers == ['lifecycle-probe']:",
                "    for token in __import__('json').loads(LIFECYCLE_ARGS):",
                "        print(token)",
                "else:",
                "    print('ERROR: unknown runnable MCP server: ' + ','.join(servers), file=sys.stderr)",
                "    raise SystemExit(2)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    helper.chmod(0o755)
    return helper


def write_fake_codex(root: Path) -> Path:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    script = bin_dir / "codex"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json",
                "import os",
                "import subprocess",
                "import sys",
                "import time",
                "",
                "if sys.argv[1:3] == ['exec', '--help']:",
                "    print('usage: codex exec --output-last-message <file>')",
                "    raise SystemExit(0)",
                "",
                "configs = []",
                "last_message_path = ''",
                "index = 1",
                "while index < len(sys.argv):",
                "    if sys.argv[index] == '-c':",
                "        configs.append(sys.argv[index + 1])",
                "        index += 2",
                "    elif sys.argv[index] == '--output-last-message':",
                "        last_message_path = sys.argv[index + 1]",
                "        index += 2",
                "    else:",
                "        index += 1",
                "",
                "sys.stdin.read()",
                "command = ''",
                "args = []",
                "for config in configs:",
                "    if config == 'mcp_servers={}':",
                "        continue",
                "    if config.startswith('mcp_servers.lifecycle-probe.command='):",
                "        command = json.loads(config.split('=', 1)[1])",
                "    elif config.startswith('mcp_servers.lifecycle-probe.args='):",
                "        args = json.loads(config.split('=', 1)[1])",
                "",
                "mcp_proc = None",
                "if command:",
                "    mcp_proc = subprocess.Popen([command, *args])",
                "",
                "mode = os.environ.get('FAKE_CODEX_MODE', 'complete')",
                "if mode == 'timeout':",
                "    time.sleep(30)",
                "    raise SystemExit(0)",
                "",
                "if mcp_proc is not None:",
                "    time.sleep(0.2)",
                "    mcp_proc.terminate()",
                "    try:",
                "        mcp_proc.wait(timeout=3)",
                "    except subprocess.TimeoutExpired:",
                "        mcp_proc.kill()",
                "        mcp_proc.wait(timeout=3)",
                "",
                "message = '\\n'.join([",
                "    '검증 명령/결과: fake codex MCP lifecycle => passed',",
                "    '최종 산출물 경로: .agents/skills/harness/run-all-tests/tests/test_mcp_lifecycle.py',",
                "    '마지막 checkpoint 요약: fake lifecycle probe completed',",
                "    '<promise>HARNESS_COMPLETE</promise>',",
                "])",
                "if last_message_path:",
                "    open(last_message_path, 'w', encoding='utf-8').write(message)",
                "else:",
                "    print(message)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir


def configure_fake_codex(monkeypatch: pytest.MonkeyPatch, bin_dir: Path, mode: str = "complete") -> None:
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("FAKE_CODEX_MODE", mode)
    monkeypatch.setattr(CodexAdapter, "_output_last_message_supported", None)


def wait_for_pid_exit(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def read_pid(marker_dir: Path) -> int:
    return int((marker_dir / "pid").read_text(encoding="utf-8"))


def test_selected_command_mcp_starts_and_stops_on_loop_completion(tmp_path, monkeypatch):
    marker_dir = tmp_path / "markers"
    fake_mcp = write_fake_mcp(tmp_path)
    write_lifecycle_mcp_render_helper(tmp_path, fake_mcp, marker_dir)
    bin_dir = write_fake_codex(tmp_path)
    configure_fake_codex(monkeypatch, bin_dir)
    plan_path = write_reviewed_active_plan(tmp_path, mcp_servers="[lifecycle-probe]")
    loop, state_file = make_loop(tmp_path, plan_path)

    assert loop.run() == 0

    loaded = LoopState.from_file(state_file)
    assert loaded.stop_reason == "completed"
    assert loaded.mcp_servers == '["lifecycle-probe"]'
    assert (marker_dir / "started").exists()
    assert (marker_dir / "stopped").exists()
    assert wait_for_pid_exit(read_pid(marker_dir))
    loop_events = events(tmp_path)
    assert loop_events[0]["mcp_servers"] == '["lifecycle-probe"]'
    assert loop_events[1]["mcp_servers"] == '["lifecycle-probe"]'


def test_command_mcp_is_killed_when_codex_child_times_out(tmp_path, monkeypatch):
    marker_dir = tmp_path / "markers"
    fake_mcp = write_fake_mcp(tmp_path)
    bin_dir = write_fake_codex(tmp_path)
    configure_fake_codex(monkeypatch, bin_dir, mode="timeout")
    adapter = CodexAdapter(lifecycle_mcp_args(fake_mcp, marker_dir))

    exit_code, output = adapter.run("prompt", timeout=1)

    assert exit_code == -1
    assert "[cleanup] process_group_terminated" in output
    assert (marker_dir / "started").exists()
    assert not (marker_dir / "stopped").exists()
    assert wait_for_pid_exit(read_pid(marker_dir))


def test_mcp_free_loop_does_not_start_lifecycle_probe(tmp_path, monkeypatch):
    marker_dir = tmp_path / "markers"
    fake_mcp = write_fake_mcp(tmp_path)
    write_lifecycle_mcp_render_helper(tmp_path, fake_mcp, marker_dir)
    bin_dir = write_fake_codex(tmp_path)
    configure_fake_codex(monkeypatch, bin_dir)
    plan_path = write_reviewed_active_plan(tmp_path, mcp_servers="[]")
    loop, state_file = make_loop(tmp_path, plan_path)

    assert loop.run() == 0

    loaded = LoopState.from_file(state_file)
    assert loaded.stop_reason == "completed"
    assert loaded.mcp_servers == "[]"
    assert not (marker_dir / "started").exists()
    assert not (marker_dir / "pid").exists()
    assert events(tmp_path)[0]["mcp_servers"] == "[]"
