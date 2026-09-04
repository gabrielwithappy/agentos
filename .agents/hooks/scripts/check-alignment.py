import glob
import hashlib
import os
import re
import sys
from pathlib import Path

REVIEWED_RE = re.compile(r"^> reviewed: true(?:\s*<br\s*/?>)?$", re.MULTILINE)
REVIEWED_META_RE = re.compile(r"^> reviewed: (?:true|false)(?:\s*<br\s*/?>)?$", re.MULTILINE)
HEADER_STATUS_RE = re.compile(r"^> \*\*상태:\*\* .+$", re.MULTILINE)
GATE2_RE = re.compile(r"^> gate2_[^:\n]+:.*$", re.MULTILINE)
# Fields/sections that other harness contracts require agents to fill in
# AFTER Gate 2 signing: implementation_*_at/duration, active_agent,
# active_session (executing-plans/SKILL.md Step 7-8 occupancy lock),
# dashboard_item_id (TEMPLATE.md, auto-written by `agentos dashboard
# sync-plan`), Task checkbox state, and the "Completed Active Plan Closeout"
# prose sections (writing-plans/SKILL.md). Excluded from the hash so a
# properly closed-out plan doesn't retroactively invalidate its own review.
#
# Threat model: this exclusion is intentionally unbounded in content (a
# timestamp/id line or a closeout section can hold arbitrary text) but
# bounded in *what it can influence* — no code in this harness parses these
# fields/sections as directives; they are display/bookkeeping only. The
# content that actually specifies what was reviewed and approved (목표,
# 아키텍처, Task steps, 사용자 결과, 의존성 게이트, etc.) is NOT matched by
# any of these patterns and remains fully hashed, so tampering with scope
# after signing still invalidates the signature.
#
# Kept in sync with the copy in
# .agents/skills/harness/writing-plans/scripts/review_artifacts.py.
LIVING_META_RE = re.compile(
    r"^> (?:implementation_started_at|implementation_completed_at|implementation_duration|"
    r"dashboard_item_id|active_agent|active_session): .*$",
    re.MULTILINE,
)
TASK_CHECKBOX_RE = re.compile(r"^(\s*-\s*)\[[ xX]\]", re.MULTILINE)
LIVING_SECTION_RE = re.compile(
    r"^##\s*(?:진행 스냅샷|구현 결과|사용 방법|완료 증거|아카이브 결정)\s*\n.*?(?=\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)


def normalize_plan_text(text: str) -> str:
    normalized = REVIEWED_META_RE.sub("", text)
    normalized = GATE2_RE.sub("", normalized)
    normalized = HEADER_STATUS_RE.sub("", normalized)
    normalized = LIVING_META_RE.sub("", normalized)
    normalized = TASK_CHECKBOX_RE.sub(r"\1[ ]", normalized)
    normalized = LIVING_SECTION_RE.sub("", normalized)
    lines = [line.rstrip() for line in normalized.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def plan_hash(text: str) -> str:
    return hashlib.sha256(normalize_plan_text(text).encode("utf-8")).hexdigest()


def plan_slug(plan_path: str) -> str:
    name = Path(plan_path).stem
    if name.endswith(".ko"):
        name = name[:-3]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "plan"


def get_target_plans(root: Path) -> list[str]:
    loop_state_file = root / ".agents" / "traces" / "harness" / "loop-state.md"
    if loop_state_file.is_file():
        match = re.search(r'^plan_path:\s*"([^"]*)"$', loop_state_file.read_text(encoding="utf-8"), re.MULTILINE)
        if match and match.group(1):
            target = match.group(1)
            if (root / target).is_file():
                return [target]

    active_plans = sorted(glob.glob(".agentos/project/exec-plans/active/*.md"))
    reviewed_plans = []
    for plan_str in active_plans:
        content = Path(plan_str).read_text(encoding="utf-8")
        if REVIEWED_RE.search(content):
            reviewed_plans.append(plan_str)
    return reviewed_plans


def check_alignment() -> int:
    root = Path(os.getcwd())
    target_plans = get_target_plans(root)
    if not target_plans:
        print(
            "AgentOS Unified Hook [Alignment]: No active reviewed plan found. Did you confirm the design with the user?",
            file=sys.stderr,
        )
        return 0

    scripts_dir = root / ".agents" / "skills" / "harness" / "writing-plans" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from review_artifacts import check_plan, dispatch

    for plan_str in target_plans:
        plan_path = Path(plan_str)
        rel_path = plan_path.relative_to(root).as_posix() if plan_path.is_absolute() else plan_str
        try:
            # Enforce dispatch --stage final with plan-reviewer-final adjudication before execution
            if dispatch(root, rel_path, "final") != 0:
                raise ValueError("dispatch --stage final failed: missing handoff or plan-reviewer-final adjudication")
            if not check_plan(root, rel_path).valid:
                raise ValueError("invalid review evidence")
        except Exception:
            print(
                f"AgentOS Unified Hook [Alignment]: Review evidence for {rel_path} is missing or out of date; do not execute. Request the required independent reviews and, for a protected change, independent architect approval; then run python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan {rel_path}.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(check_alignment())
