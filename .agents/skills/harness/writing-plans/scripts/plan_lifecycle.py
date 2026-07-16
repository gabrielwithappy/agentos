#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_artifacts import check_plan


STATUS_RE = re.compile(r"^> \*\*상태:\*\* (.+?)(?:\s*<br\s*/?>)?$", re.MULTILINE)
REVIEWED_RE = re.compile(r"^> reviewed: true(?:\s*<br\s*/?>)?$", re.MULTILINE)
TITLE_RE = re.compile(r"^# (.+)$", re.MULTILINE)
USER_OUTCOME_RES = [
    re.compile(r"^\*\*사용자 결과:\*\*\s*(.+)$", re.MULTILINE),
    re.compile(r"^\*\*사용자가 얻게 되는 결과:\*\*\s*(.+)$", re.MULTILINE),
    re.compile(r"^\*\*User-Visible Outcome:\*\*\s*(.+)$", re.MULTILINE),
]
PROGRESS_RES = [
    re.compile(r"^\*\*진행 상태:\*\*\s*(.+)$", re.MULTILINE),
    re.compile(r"^\*\*Progress:\*\*\s*(.+)$", re.MULTILINE),
]
ALLOWED_STATUSES = {
    "계획 초안",
    "구현 계획 (agent 분석 반영, 리뷰 완료)",
    "구현 계획 (리뷰 대기)",
    "구현 계획 (리뷰 완료)",
    "구현 계획 (실행 대기)",
    "설계 문서 (구현 미정)",
    "아키텍처 분석 문서",
    "완료",
    "통합 구현 계획",
    "통합됨",
    "보관됨",
}
ACTIVE_PREFIX = ".agentos/project/exec-plans/active/"
ARCHIVE_PREFIX = ".agentos/project/exec-plans/archive/"
REFERENCE_ARCHIVE_PREFIX = ".agentos/project/exec-plans/archive/reference/"
EXEC_BOARD_ACTIVE_RECENT_LIMIT = 20
EXEC_BOARD_ARCHIVED_RECENT_LIMIT = 20
EXEC_BOARD_REFERENCE_RECENT_LIMIT = 10


@dataclass
class PlanEntry:
    path: str
    status: str
    title: str
    reviewed: bool = False
    reviewed_header: bool = False
    review_evidence_status: str | None = None
    user_outcome: str | None = None
    progress: str | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "path": self.path,
            "status": self.status,
            "title": self.title,
        }
        if self.reviewed:
            data["reviewed"] = True
        if self.reviewed_header and not self.reviewed:
            data["reviewed_header"] = True
        if self.review_evidence_status:
            data["review_evidence_status"] = self.review_evidence_status
        if self.user_outcome:
            data["user_outcome"] = self.user_outcome
        if self.progress:
            data["progress"] = self.progress
        return data


def parse_plan(path: Path, root: Path) -> PlanEntry | None:
    if path.name == "README.md":
        return None

    text = path.read_text(encoding="utf-8")
    title_match = TITLE_RE.search(text)
    status_match = STATUS_RE.search(text)
    user_outcome_match = first_match(USER_OUTCOME_RES, text)
    progress_match = first_match(PROGRESS_RES, text)
    if not title_match or not status_match:
        return None

    rel_path = path.relative_to(root).as_posix()
    reviewed_header = bool(REVIEWED_RE.search(text))
    review_check = check_plan(root, rel_path) if reviewed_header else None
    return PlanEntry(
        path=rel_path,
        status=status_match.group(1).strip(),
        title=title_match.group(1).strip(),
        reviewed=bool(review_check and review_check.valid),
        reviewed_header=reviewed_header,
        review_evidence_status=(review_check.status if review_check and not review_check.valid else None),
        user_outcome=user_outcome_match.group(1).strip() if user_outcome_match else None,
        progress=progress_match.group(1).strip() if progress_match else None,
    )


def first_match(patterns: list[re.Pattern[str]], text: str) -> re.Match[str] | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match
    return None


def classify_plan(entry: PlanEntry) -> str:
    if entry.path.startswith(REFERENCE_ARCHIVE_PREFIX):
        return "reference"
    if entry.path.startswith(ARCHIVE_PREFIX):
        return "archived"
    if entry.path.startswith(ACTIVE_PREFIX):
        return "active"
    return "reference"


def collect_plans(root: Path) -> tuple[list[PlanEntry], list[PlanEntry], list[PlanEntry]]:
    exec_plans_dir = root / ".agentos" / "project" / "exec-plans"
    active: list[PlanEntry] = []
    reference: list[PlanEntry] = []
    archived: list[PlanEntry] = []

    for path in sorted(exec_plans_dir.rglob("*.md")):
        entry = parse_plan(path, root)
        if entry is None:
            continue
        bucket = classify_plan(entry)
        if bucket == "active":
            active.append(entry)
        elif bucket == "archived":
            archived.append(entry)
        else:
            reference.append(entry)
    return active, reference, archived


def load_loop_state_plan_path(root: Path) -> str | None:
    path = root / ".agents" / "traces" / "harness" / "loop-state.md"
    if not path.exists():
        return None
    match = re.search(r'^plan_path: "([^"]*)"$', path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match or not match.group(1):
        return None
    return match.group(1)


def detect_current_plan(active: list[PlanEntry], raw_plan_path: str | None) -> str | None:
    if not raw_plan_path:
        return None
    active_paths = {entry.path for entry in active}
    return raw_plan_path if raw_plan_path in active_paths else None


def build_current_plan_warning(active: list[PlanEntry], raw_plan_path: str | None) -> dict[str, str] | None:
    if not raw_plan_path:
        return None
    active_paths = {entry.path for entry in active}
    if raw_plan_path in active_paths:
        return None
    return {
        "type": "plan_path_mismatch",
        "plan_path": raw_plan_path,
    }


def build_archived_summary(archived: list[PlanEntry]) -> dict[str, int]:
    completed = sum(1 for entry in archived if entry.status == "완료")
    parked = len(archived) - completed
    return {
        "completed": completed,
        "parked": parked,
    }


def build_plan_json(root: Path, active: list[PlanEntry], reference: list[PlanEntry], archived: list[PlanEntry]) -> dict[str, object]:
    raw_plan_path = load_loop_state_plan_path(root)
    current_plan = detect_current_plan(active, raw_plan_path)
    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_plan": current_plan,
        "active_plans": [entry.to_dict() for entry in active],
        "reference_plans": [entry.to_dict() for entry in reference],
        "archived_plans": [entry.to_dict() for entry in archived],
        "archived_summary": build_archived_summary(archived),
    }
    warning = build_current_plan_warning(active, raw_plan_path)
    if warning:
        data["current_plan_warning"] = warning
    return data


def format_summary(value: str, limit: int = 140) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def format_plan_link(entry: PlanEntry) -> str:
    extras: list[str] = []
    if entry.reviewed:
        extras.append("reviewed")
    elif entry.reviewed_header and entry.review_evidence_status:
        extras.append(f"reviewed_evidence={entry.review_evidence_status}")
    if entry.user_outcome:
        extras.append(f"outcome: {format_summary(entry.user_outcome)}")
    if entry.progress:
        extras.append(f"progress: {format_summary(entry.progress)}")
    suffix = " | " + " | ".join(extras) if extras else ""
    return f"- `{entry.status}` [{entry.title}]({entry.path}){suffix}"


def recent_window(entries: list[PlanEntry], limit: int) -> tuple[list[PlanEntry], int]:
    if limit <= 0:
        return [], len(entries)
    if len(entries) <= limit:
        return list(reversed(entries)), 0
    return list(reversed(entries[-limit:])), len(entries) - limit


def build_readme(data: dict[str, object]) -> str:
    generated_at = data["generated_at"]
    current_plan = data["current_plan"]
    current_plan_warning = data.get("current_plan_warning")
    active = [PlanEntry(**entry) for entry in data["active_plans"]]
    reference = [PlanEntry(**entry) for entry in data["reference_plans"]]
    archived = [PlanEntry(**entry) for entry in data["archived_plans"]]
    archived_summary = data["archived_summary"]
    active_recent, active_omitted = recent_window(active, EXEC_BOARD_ACTIVE_RECENT_LIMIT)
    archived_recent, archived_omitted = recent_window(archived, EXEC_BOARD_ARCHIVED_RECENT_LIMIT)
    reference_recent, reference_omitted = recent_window(reference, EXEC_BOARD_REFERENCE_RECENT_LIMIT)

    lines = [
        "# Exec Plans Board",
        "",
        "> 자동 생성 문서. 수동 편집하지 마세요.",
        "> Source of truth: `.agents/mission/plan.json`",
        "",
        f"> Generated at: {generated_at}",
        "",
        "## Active Plans",
    ]

    if current_plan:
        lines.append(f"- 현재 실행 중: `{current_plan}`")
    elif not active:
        lines.append("- 현재 실행 중인 계획 없음")
    if current_plan_warning:
        lines.append(
            f"- warning: plan_path mismatch (`{current_plan_warning['plan_path']}`) is not in active registry"
        )
    lines.append(f"- older active plans omitted={active_omitted}")
    for entry in active_recent:
        lines.append(format_plan_link(entry))

    lines.extend(["", "## Archived Plans"])
    lines.append(
        f"- archive summary: completed={archived_summary['completed']}, parked={archived_summary['parked']}"
    )
    lines.append(f"- older archived plans omitted={archived_omitted}")
    if archived_recent:
        for entry in archived_recent:
            lines.append(format_plan_link(entry))
    else:
        lines.append("- archived plans 없음")

    lines.extend(["", "## Reference Docs"])
    lines.append(f"- older reference docs omitted={reference_omitted}")
    if reference_recent:
        for entry in reference_recent:
            lines.append(format_plan_link(entry))
    else:
        lines.append("- reference docs 없음")

    lines.append("")
    return "\n".join(lines)


def refresh(root: Path) -> None:
    active, reference, archived = collect_plans(root)
    plan_json = build_plan_json(root, active, reference, archived)

    mission_dir = root / ".agents" / "mission"
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "plan.json").write_text(
        json.dumps(plan_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme_path = root / ".agentos" / "project" / "exec-plans" / "README.md"
    readme_path.write_text(build_readme(plan_json), encoding="utf-8")


def resolve_plan_path(root: Path, plan_path: str) -> Path:
    path = (root / plan_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {plan_path}") from exc
    if not path.exists():
        raise ValueError(f"plan not found: {plan_path}")
    if not path.is_file():
        raise ValueError(f"plan is not a file: {plan_path}")
    return path


def validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid status: {status}")


def replace_status(text: str, status: str) -> str:
    updated, count = STATUS_RE.subn(f"> **상태:** {status}", text, count=1)
    if count != 1:
        raise ValueError("status header not found")
    return updated


def set_status(root: Path, plan_path: str, status: str) -> None:
    validate_status(status)
    path = resolve_plan_path(root, plan_path)
    current_entry = parse_plan(path, root)
    if current_entry is None:
        raise ValueError("plan header is incomplete")
    if status == "진행 중":
        raise ValueError("진행 중 status is no longer supported; use loop-state plan_path for runtime tracking")

    updated = replace_status(path.read_text(encoding="utf-8"), status)
    path.write_text(updated, encoding="utf-8")
    refresh(root)


def archive_plan(root: Path, plan_path: str, status: str) -> None:
    if status != "완료":
        raise ValueError("archive only supports --status 완료")

    path = resolve_plan_path(root, plan_path)
    rel_path = path.relative_to(root).as_posix()
    if rel_path.startswith(ARCHIVE_PREFIX):
        raise ValueError(f"plan is already archived: {plan_path}")

    archive_dir = root / ".agentos" / "project" / "exec-plans" / "archive"
    destination = archive_dir / path.name
    if destination.exists():
        raise ValueError(f"archive destination already exists: {destination.relative_to(root).as_posix()}")

    updated = replace_status(path.read_text(encoding="utf-8"), "완료")
    archive_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    shutil.move(str(path), str(destination))
    refresh(root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh exec-plan lifecycle artifacts")
    parser.add_argument("command", choices=["refresh", "set-status", "archive"])
    parser.add_argument("plan_path", nargs="?")
    parser.add_argument("status", nargs="?")
    parser.add_argument("--status", dest="status_flag")
    parser.add_argument(
        "--root",
        default=None,
        help="Project root. Defaults to git top-level or this script's repo root.",
    )
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[5]

    try:
        if args.command == "refresh":
            refresh(root)
        elif args.command == "set-status":
            if not args.plan_path or not args.status:
                raise ValueError("set-status requires <plan-path> <status>")
            set_status(root, args.plan_path, args.status)
        elif args.command == "archive":
            if not args.plan_path:
                raise ValueError("archive requires <plan-path>")
            archive_plan(root, args.plan_path, args.status_flag or "완료")
    except ValueError as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
