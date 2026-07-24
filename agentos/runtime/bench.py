from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

from agentos.llm.invocation import invoke_once
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event
from agentos.runtime.launcher import resolve_agentos_launcher
from agentos.runtime.protocol import RuntimeRequest


PASS_THRESHOLD_MS = 250.0
SESSION_RUNTIME_CONTEXT_BUILD_P95_MS = 50.0
SESSION_RUNTIME_FIRST_EVENT_DELTA_MS = 250.0


@dataclass(frozen=True)
class PhaseMeasurement:
    label: str
    bootstrap_ms: float
    first_event_ms: float
    provider_ms: float
    persistence_ms: float = 0.0
    total_ms: float = 0.0
    available: bool = True
    status: str = "ok"
    recovery: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "label": self.label,
            "bootstrap_ms": round(self.bootstrap_ms, 3),
            "first_event_ms": round(self.first_event_ms, 3),
            "provider_ms": round(self.provider_ms, 3),
            "persistence_ms": round(self.persistence_ms, 3),
            "total_ms": round(self.total_ms, 3),
            "available": self.available,
            "status": self.status,
        }
        if self.recovery:
            payload["recovery"] = self.recovery
        return payload


def _measure_provider(prompt: str, provider: str) -> PhaseMeasurement:
    started = time.perf_counter()
    first_event_at: float | None = None
    status = "ok"
    recovery = None
    try:
        for event in stream_once(prompt, provider=provider):
            if first_event_at is None:
                first_event_at = time.perf_counter()
            if event.type == "error":
                status = event.error.get("code", "error") if event.error else "error"
                recovery = event.recovery
    except UnsupportedProviderError:
        first_event_at = time.perf_counter()
        event = unsupported_provider_event(provider)
        status = event.error["code"] if event.error else "unsupported_provider"
        recovery = event.recovery
    finished = time.perf_counter()
    first = first_event_at or finished
    return PhaseMeasurement(
        label="direct_provider",
        bootstrap_ms=0.0,
        first_event_ms=(first - started) * 1000,
        provider_ms=(finished - started) * 1000,
        total_ms=(finished - started) * 1000,
        status=status,
        recovery=recovery,
    )


def _measure_runtime(prompt: str, provider: str) -> PhaseMeasurement:
    started = time.perf_counter()
    first_event_at: float | None = None
    status = "ok"
    recovery = None
    request = RuntimeRequest(
        prompt=prompt,
        provider=provider,
        transport_hint="runtime_warm",
        record_policy="metadata",
    )
    try:
        for event in invoke_once(request):
            if first_event_at is None:
                first_event_at = time.perf_counter()
            if event.type == "error":
                status = event.error.get("code", "error") if event.error else "error"
                recovery = event.recovery
    except UnsupportedProviderError:
        first_event_at = time.perf_counter()
        event = unsupported_provider_event(provider)
        status = event.error["code"] if event.error else "unsupported_provider"
        recovery = event.recovery
    finished = time.perf_counter()
    first = first_event_at or finished
    return PhaseMeasurement(
        label="runtime_warm",
        bootstrap_ms=0.0,
        first_event_ms=(first - started) * 1000,
        provider_ms=(finished - started) * 1000,
        total_ms=(finished - started) * 1000,
        status=status,
        recovery=recovery,
    )


def _measure_command(
    label: str,
    command: list[str],
    timeout_seconds: int = 30,
    *,
    require_canonical_agentos: bool = False,
) -> PhaseMeasurement:
    if require_canonical_agentos and command[0] == "agentos":
        launcher = resolve_agentos_launcher()
        if not launcher.installed:
            return PhaseMeasurement(
                label=label,
                bootstrap_ms=0.0,
                first_event_ms=0.0,
                provider_ms=0.0,
                total_ms=0.0,
                available=False,
                status=launcher.status,
                recovery=launcher.recovery,
            )
        executable = launcher.executable
    else:
        executable = shutil.which(command[0])
    if executable is None:
        return PhaseMeasurement(
            label=label,
            bootstrap_ms=0.0,
            first_event_ms=0.0,
            provider_ms=0.0,
            total_ms=0.0,
            available=False,
            status="missing_launcher",
            recovery="Use installed agentos for canonical runs, or uv run for development-only runs.",
        )
    started = time.perf_counter()
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        status = "ok" if result.returncode == 0 else f"exit_{result.returncode}"
    except subprocess.TimeoutExpired:
        status = "timeout"
    finished = time.perf_counter()
    elapsed_ms = (finished - started) * 1000
    return PhaseMeasurement(
        label=label,
        bootstrap_ms=elapsed_ms,
        first_event_ms=elapsed_ms,
        provider_ms=elapsed_ms,
        total_ms=elapsed_ms,
        status=status,
    )


def capture_benchmark(prompt: str, provider: str) -> dict[str, Any]:
    direct_provider = _measure_provider(prompt, provider)
    runtime_warm = _measure_runtime(prompt, provider)
    uv_run = _measure_command(
        "uv_run",
        ["uv", "run", "agentos", "run", "--once", "--json", "--provider", provider, prompt],
    )
    installed_cli = _measure_command(
        "installed_cli",
        ["agentos", "run", "--once", "--json", "--provider", provider, prompt],
        require_canonical_agentos=True,
    )
    return {
        "schema_version": "agentos.invocation-benchmark/v1",
        "provider": provider,
        "threshold_ms": PASS_THRESHOLD_MS,
        "uv_run": uv_run.to_dict(),
        "installed_cli": installed_cli.to_dict(),
        "direct_provider": direct_provider.to_dict(),
        "runtime_warm": runtime_warm.to_dict(),
        "go_no_go": benchmark_decision(uv_run, runtime_warm),
    }


def benchmark_decision(uv_run: PhaseMeasurement, runtime_warm: PhaseMeasurement) -> dict[str, Any]:
    delta_ms = uv_run.first_event_ms - runtime_warm.first_event_ms
    passed = delta_ms >= PASS_THRESHOLD_MS and runtime_warm.bootstrap_ms < uv_run.bootstrap_ms
    return {
        "warm_path_pass": passed,
        "delta_ms": round(delta_ms, 3),
        "required_delta_ms": PASS_THRESHOLD_MS,
        "next_action": (
            "PASS invocation-runtime-benchmark"
            if passed
            else "Do not start daemon/server-client migration; keep external CLI compatibility path and record benchmark evidence."
        ),
    }


@dataclass(frozen=True)
class SessionRuntimeSample:
    """One measured second-turn timing sample from a two-turn marker-recall
    trial (first turn plants `AGENTOS_SESSION_MARKER`, second turn asks for
    it back). `mode` records whether continuation reuse was allowed for
    this trial's second turn, or forced off (`force_full_replay=True`) for
    an explicit full-context-replay comparison point."""

    trial: int
    mode: str  # "continuation" | "full_replay"
    context_build_ms: float
    first_event_ms: float
    marker_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial": self.trial,
            "mode": self.mode,
            "context_build_ms": round(self.context_build_ms, 3),
            "first_event_ms": round(self.first_event_ms, 3),
            "marker_preserved": self.marker_preserved,
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def _extract_marker(first_prompt: str) -> str:
    if "AGENTOS_SESSION_MARKER=" not in first_prompt:
        return ""
    tail = first_prompt.split("AGENTOS_SESSION_MARKER=", 1)[1]
    return tail.rstrip(".").split()[0] if tail.strip() else ""


def _run_session_runtime_trial(
    *, provider: str, model: str, first_prompt: str, second_prompt: str, trial: int, force_full_replay: bool
) -> SessionRuntimeSample:
    from agentos.conversation.persistence import empty_state
    from agentos.conversation.runtime import ConversationRuntime

    runtime = ConversationRuntime(
        empty_state(f"session-runtime-bench-{trial}"), provider=provider, model=model
    )
    for _ in runtime.submit_turn(first_prompt):
        pass

    started = time.perf_counter()
    first_event_at: float | None = None
    response_text_parts: list[str] = []
    for event in runtime.submit_turn(second_prompt, force_full_replay=force_full_replay):
        if first_event_at is None:
            first_event_at = time.perf_counter()
        if event.type == "message_delta" and event.text:
            response_text_parts.append(event.text)
    finished = time.perf_counter()

    marker = _extract_marker(first_prompt)
    response_text = "".join(response_text_parts)
    return SessionRuntimeSample(
        trial=trial,
        mode="full_replay" if force_full_replay else "continuation",
        context_build_ms=runtime.last_context_build_ms or 0.0,
        first_event_ms=((first_event_at or finished) - started) * 1000,
        marker_preserved=bool(marker) and marker in response_text,
    )


def capture_session_runtime_benchmark(
    *, provider: str, model: str, first_prompt: str, second_prompt: str, runs: int = 5
) -> dict[str, Any]:
    """Runs one discarded warmup trial, then `runs` paired trials alternating
    continuation-reuse and forced-full-replay second turns, and reports
    every sample plus median/p95 `context_build_ms`/`first_event_ms`."""
    _run_session_runtime_trial(
        provider=provider,
        model=model,
        first_prompt=first_prompt,
        second_prompt=second_prompt,
        trial=0,
        force_full_replay=False,
    )

    samples = [
        _run_session_runtime_trial(
            provider=provider,
            model=model,
            first_prompt=first_prompt,
            second_prompt=second_prompt,
            trial=trial,
            force_full_replay=(trial % 2 == 1),
        )
        for trial in range(1, runs + 1)
    ]

    context_build_values = [s.context_build_ms for s in samples]
    first_event_values = [s.first_event_ms for s in samples]
    context_build_p95 = _percentile(context_build_values, 95)
    marker_preserved = all(s.marker_preserved for s in samples)
    context_build_pass = context_build_p95 <= SESSION_RUNTIME_CONTEXT_BUILD_P95_MS

    return {
        "schema_version": "agentos.session-runtime-benchmark/v1",
        "provider": provider,
        "model": model,
        "runs": runs,
        "samples": [s.to_dict() for s in samples],
        "context_build_ms": {
            "median": round(statistics.median(context_build_values), 3),
            "p95": round(context_build_p95, 3),
            "threshold_p95_ms": SESSION_RUNTIME_CONTEXT_BUILD_P95_MS,
            "pass": context_build_pass,
        },
        "first_event_ms": {
            "median": round(statistics.median(first_event_values), 3),
            "p95": round(_percentile(first_event_values, 95), 3),
        },
        "marker_preserved": marker_preserved,
        "go_no_go": {
            "pass": context_build_pass and marker_preserved,
        },
    }


def _authenticated_codex_preflight() -> bool:
    from agentos.commands.llm import build_status_payload

    return bool(build_status_payload("codex").get("authenticated") is True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure AgentOS LLM invocation phase timings.")
    parser.add_argument("--prompt")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--assert-warm-faster", action="store_true")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--first-prompt")
    parser.add_argument("--second-prompt")
    parser.add_argument("--assert-session-runtime", action="store_true")
    args = parser.parse_args(argv)

    if args.assert_session_runtime:
        return _main_session_runtime(args)

    if not args.prompt:
        parser.error("--prompt is required unless --assert-session-runtime is used.")

    payload = capture_benchmark(args.prompt, args.provider)
    if args.assert_warm_faster:
        if payload["go_no_go"]["warm_path_pass"]:
            print("PASS invocation-runtime-benchmark")
            return 0
        print(payload["go_no_go"]["next_action"])
        return 1
    if args.format == "json":
        print(json.dumps(payload, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _main_session_runtime(args: argparse.Namespace) -> int:
    if not args.first_prompt or not args.second_prompt:
        print("--first-prompt and --second-prompt are required with --assert-session-runtime.")
        return 2

    model = "gpt-5-codex" if args.provider in ("codex", "codex-cli") else f"{args.provider}-default"

    if args.provider in ("codex", "codex-cli"):
        if os.environ.get("AGENTOS_CODEX_INTEGRATION") != "1":
            print("PASS session-runtime-benchmark skipped=integration-disabled")
            return 0
        if not _authenticated_codex_preflight():
            print("STOP session-runtime-benchmark unauthenticated")
            return 2

    payload = capture_session_runtime_benchmark(
        provider=args.provider,
        model=model,
        first_prompt=args.first_prompt,
        second_prompt=args.second_prompt,
        runs=args.runs,
    )

    if args.format == "json":
        print(json.dumps(payload, sort_keys=True))

    if payload["go_no_go"]["pass"]:
        print("PASS session-runtime-benchmark")
        return 0
    print(
        "FAIL session-runtime-benchmark stop=daemon-follow-up-not-approved "
        f"context_build_p95_ms={payload['context_build_ms']['p95']} "
        f"marker_preserved={payload['marker_preserved']}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
