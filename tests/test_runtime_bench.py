import json
import os

from agentos.runtime import bench
from agentos.runtime.bench import PhaseMeasurement, benchmark_decision
from agentos.runtime.launcher import resolve_agentos_launcher


def measurement(label: str, first_event_ms: float, bootstrap_ms: float) -> PhaseMeasurement:
    return PhaseMeasurement(
        label=label,
        bootstrap_ms=bootstrap_ms,
        first_event_ms=first_event_ms,
        provider_ms=first_event_ms,
        total_ms=first_event_ms,
    )


def test_warm_runtime_overhead():
    decision = benchmark_decision(
        measurement("uv_run", first_event_ms=600, bootstrap_ms=500),
        measurement("runtime_warm", first_event_ms=100, bootstrap_ms=10),
    )

    assert decision["warm_path_pass"] is True
    assert decision["next_action"] == "PASS invocation-runtime-benchmark"


def test_launcher_phase_delta():
    decision = benchmark_decision(
        measurement("uv_run", first_event_ms=300, bootstrap_ms=250),
        measurement("runtime_warm", first_event_ms=100, bootstrap_ms=10),
    )

    assert decision["warm_path_pass"] is False
    assert "Do not start daemon/server-client migration" in decision["next_action"]


def test_capture_benchmark_schema(monkeypatch):
    monkeypatch.setattr(
        bench,
        "_measure_command",
        lambda label, command, timeout_seconds=30, **kwargs: measurement(
            label, first_event_ms=500, bootstrap_ms=400
        ),
    )

    payload = bench.capture_benchmark("hello", "mock")

    assert all(k in payload for k in ("uv_run", "installed_cli", "direct_provider", "runtime_warm"))
    assert all(
        "first_event_ms" in payload[k] and "bootstrap_ms" in payload[k]
        for k in ("uv_run", "installed_cli", "direct_provider", "runtime_warm")
    )
    assert payload["schema_version"] == "agentos.invocation-benchmark/v1"
    assert json.dumps(payload)


def test_uv_virtualenv_agentos_is_not_canonical_installed_launcher(tmp_path, monkeypatch):
    venv = tmp_path / "venv"
    bin_dir = venv / "bin"
    bin_dir.mkdir(parents=True)
    shim = bin_dir / "agentos"
    shim.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    launcher = resolve_agentos_launcher()

    assert launcher.installed is False
    assert launcher.status == "development_shim"


def test_installed_cli_measurement_rejects_uv_virtualenv_shim(tmp_path, monkeypatch):
    venv = tmp_path / "venv"
    bin_dir = venv / "bin"
    bin_dir.mkdir(parents=True)
    shim = bin_dir / "agentos"
    shim.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("PATH", str(bin_dir))

    measurement = bench._measure_command(
        "installed_cli",
        ["agentos", "run", "--once", "hello"],
        require_canonical_agentos=True,
    )

    assert measurement.available is False
    assert measurement.status == "development_shim"


# ── PI session runtime Task 7 Step 1-3: session-runtime benchmark ──────────────


def test_session_runtime_benchmark_mock_context_build_p95_under_threshold():
    payload = bench.capture_session_runtime_benchmark(
        provider="mock",
        model="mock-default",
        first_prompt="Remember AGENTOS_SESSION_MARKER=oak.",
        second_prompt="What is AGENTOS_SESSION_MARKER?",
        runs=5,
    )

    assert payload["schema_version"] == "agentos.session-runtime-benchmark/v1"
    assert len(payload["samples"]) == 5
    assert payload["context_build_ms"]["pass"] is True
    assert payload["context_build_ms"]["p95"] <= bench.SESSION_RUNTIME_CONTEXT_BUILD_P95_MS
    assert payload["marker_preserved"] is True
    assert payload["go_no_go"]["pass"] is True


def test_session_runtime_benchmark_alternates_continuation_and_full_replay_modes():
    payload = bench.capture_session_runtime_benchmark(
        provider="mock",
        model="mock-default",
        first_prompt="Remember AGENTOS_SESSION_MARKER=oak.",
        second_prompt="What is AGENTOS_SESSION_MARKER?",
        runs=4,
    )

    modes = [sample["mode"] for sample in payload["samples"]]
    assert modes == ["full_replay", "continuation", "full_replay", "continuation"]


def test_session_runtime_benchmark_marker_lost_fails_go_no_go(monkeypatch):
    payload = bench.capture_session_runtime_benchmark(
        provider="mock",
        model="mock-default",
        first_prompt="Say hello.",  # no AGENTOS_SESSION_MARKER= present
        second_prompt="What is AGENTOS_SESSION_MARKER?",
        runs=2,
    )

    assert payload["marker_preserved"] is False
    assert payload["go_no_go"]["pass"] is False


def test_session_runtime_benchmark_codex_skips_without_integration_flag(monkeypatch, capsys):
    monkeypatch.delenv("AGENTOS_CODEX_INTEGRATION", raising=False)

    exit_code = bench.main(
        [
            "--provider",
            "codex",
            "--runs",
            "5",
            "--first-prompt",
            "Remember AGENTOS_SESSION_MARKER=oak.",
            "--second-prompt",
            "What is AGENTOS_SESSION_MARKER?",
            "--assert-session-runtime",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PASS session-runtime-benchmark skipped=integration-disabled" in captured.out


def test_session_runtime_benchmark_codex_stops_when_unauthenticated(monkeypatch, capsys):
    monkeypatch.setenv("AGENTOS_CODEX_INTEGRATION", "1")
    monkeypatch.setattr(bench, "_authenticated_codex_preflight", lambda: False)

    exit_code = bench.main(
        [
            "--provider",
            "codex",
            "--runs",
            "5",
            "--first-prompt",
            "Remember AGENTOS_SESSION_MARKER=oak.",
            "--second-prompt",
            "What is AGENTOS_SESSION_MARKER?",
            "--assert-session-runtime",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "STOP session-runtime-benchmark unauthenticated" in captured.out


def test_session_runtime_benchmark_opt_in_real_smoke_never_skips_after_opt_in(monkeypatch, capsys):
    """Once opted in (AGENTOS_CODEX_INTEGRATION=1) and authenticated, the
    benchmark must run to a PASS/FAIL/STOP outcome — never silently skip."""
    monkeypatch.setenv("AGENTOS_CODEX_INTEGRATION", "1")
    monkeypatch.setattr(bench, "_authenticated_codex_preflight", lambda: True)
    monkeypatch.setattr(
        bench,
        "capture_session_runtime_benchmark",
        lambda **kwargs: {
            "context_build_ms": {"p95": 1.0},
            "marker_preserved": True,
            "go_no_go": {"pass": True},
        },
    )

    exit_code = bench.main(
        [
            "--provider",
            "codex",
            "--runs",
            "5",
            "--first-prompt",
            "Remember AGENTOS_SESSION_MARKER=oak.",
            "--second-prompt",
            "What is AGENTOS_SESSION_MARKER?",
            "--assert-session-runtime",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PASS session-runtime-benchmark" in captured.out
    assert "skipped" not in captured.out
