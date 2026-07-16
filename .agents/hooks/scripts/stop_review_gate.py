#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "skills" / "harness" / "writing-plans" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from review_artifacts import REVIEWED_RE, check_plan
except ModuleNotFoundError:
    # Project-local hook installs intentionally omit the full harness skill tree.
    # They still must run safely for projects with no reviewed exec-plan; a full
    # harness install supplies the authoritative artifact validator above.
    REVIEWED_RE = re.compile(r"^>\s*reviewed:\s*true\s*$", re.MULTILINE)

    class _MissingArtifacts:
        valid = False
        missing = ("review-artifacts-unavailable",)
        invalid = ()

    def check_plan(_root: Path, _plan: str) -> _MissingArtifacts:
        return _MissingArtifacts()


COMPLETION_PATTERNS = (
    r"\bdone\b",
    r"\bcomplete(?:d)?\b",
    r"\bfinished\b",
    r"\bfixed\b",
    r"\bpass(?:es|ed)?\b",
    r"완료",
    r"끝났",
    r"수정했",
    r"해결했",
    r"성공",
    r"통과",
)

VERIFICATION_PATTERNS = (
    r"\btest(?:s)?\b",
    r"\bbuild\b",
    r"\bverified?\b",
    r"\bverification\b",
    r"\bexit code\b",
    r"\bpassed\b",
    r"\bran\b",
    r"검증",
    r"테스트",
    r"빌드",
    r"실행",
)


def _load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _git_dirty(cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return bool(result.stdout.strip())


def _mentions_completion(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in COMPLETION_PATTERNS)


def _mentions_verification(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in VERIFICATION_PATTERNS)


def _loop_locked(cwd: str) -> bool:
    loop_state = Path(cwd) / ".agents" / "traces" / "harness" / "loop-state.md"
    if not loop_state.exists():
        return False
    try:
        return "execution_locked: true" in loop_state.read_text()
    except OSError:
        return False


def _invalid_reviewed_plan(cwd: str) -> tuple[str, str] | None:
    active_dir = Path(cwd) / ".agentos" / "project" / "exec-plans" / "active"
    if not active_dir.is_dir():
        return None
    for path in sorted(active_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not REVIEWED_RE.search(text):
            continue
        rel = path.relative_to(cwd).as_posix()
        check = check_plan(Path(cwd), rel)
        if check.valid:
            continue
        detail = []
        if check.missing:
            detail.append(f"missing={','.join(check.missing)}")
        if check.invalid:
            detail.append(
                "invalid="
                + ",".join(f"{key}:{value}" for key, value in sorted(check.invalid.items()))
            )
        return rel, " ".join(detail) or check.status
    return None


def main() -> int:
    payload = _load_payload()
    if payload.get("stop_hook_active"):
        print(json.dumps({"continue": True}))
        return 0

    cwd = payload.get("cwd") or "."
    last_message = payload.get("last_assistant_message") or ""

    if _loop_locked(cwd):
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "The harness loop is still execution-locked. Re-check "
                        ".agents/traces/harness/loop-state.md and explain the lock "
                        "state before ending this turn."
                    ),
                }
            )
        )
        return 0

    invalid_review = _invalid_reviewed_plan(cwd)
    if invalid_review:
        plan_path, detail = invalid_review
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "Active plan has `reviewed: true` without valid independent review evidence. "
                        f"Fix {plan_path} ({detail}) before ending this turn."
                    ),
                }
            )
        )
        return 0

    if _git_dirty(cwd) and _mentions_completion(last_message) and not _mentions_verification(last_message):
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "Before ending, report the actual verification status with evidence. "
                        "If you did not run fresh verification, say that plainly instead of "
                        "implying the work is complete."
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
