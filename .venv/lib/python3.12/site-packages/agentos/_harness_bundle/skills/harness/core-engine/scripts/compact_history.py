#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


KEEP_RECENT_LINES = 200
DEFAULT_HISTORY_PATH = Path("HISTORY.md")
DEFAULT_ARCHIVE_DIR = Path("docs/project/reference/history")


@dataclass
class CompactionResult:
    original_lines: int
    archived_lines: int
    retained_lines: int
    archive_path: Path
    removed_prefix_sha256: str


def default_archive_path(now: datetime | None = None) -> Path:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m")
    return DEFAULT_ARCHIVE_DIR / f"{stamp}-history-archive.md"


def build_archive_payload(
    history_path: Path,
    original_lines: list[str],
    keep_recent_lines: int,
    archive_path: Path,
) -> tuple[str, CompactionResult]:
    retained_lines = original_lines[-keep_recent_lines:]
    archived_lines = original_lines[:-keep_recent_lines]
    removed_prefix = "\n".join(archived_lines) + ("\n" if archived_lines else "")
    removed_prefix_sha256 = hashlib.sha256(removed_prefix.encode("utf-8")).hexdigest()
    payload = "\n".join(
        [
            "# HISTORY Raw Archive",
            "",
            f"source_path={history_path.as_posix()}",
            f"archive_path={archive_path.as_posix()}",
            f"original_lines={len(original_lines)}",
            f"archived_lines={len(archived_lines)}",
            f"retained_lines={len(retained_lines)}",
            f"removed_prefix_sha256={removed_prefix_sha256}",
            "",
            "## Archived Payload",
            "```text",
            *archived_lines,
            "```",
            "",
        ]
    )
    return payload, CompactionResult(
        original_lines=len(original_lines),
        archived_lines=len(archived_lines),
        retained_lines=len(retained_lines),
        archive_path=archive_path,
        removed_prefix_sha256=removed_prefix_sha256,
    )


def build_recent_window(history_path: Path, archive_path: Path, retained_lines: list[str]) -> str:
    lines = [
        "# Harness Evolution History",
        "> recent operational window only",
        f"> archive: {archive_path.as_posix()}",
        "> distilled intelligence: .agents/skills/harness/brain/lessons-learned.md",
        "",
        f"archive: {archive_path.as_posix()}",
        f"source_path: {history_path.as_posix()}",
        f"retained_recent_lines: {len(retained_lines)}",
        "",
        "## Recent Window",
        *retained_lines,
        "",
    ]
    return "\n".join(lines)


def compact_history(history_path: Path, archive_path: Path, keep_recent_lines: int) -> CompactionResult:
    history_text = history_path.read_text(encoding="utf-8")
    original_lines = history_text.splitlines()
    if len(original_lines) <= keep_recent_lines:
        return CompactionResult(
            original_lines=len(original_lines),
            archived_lines=0,
            retained_lines=len(original_lines),
            archive_path=archive_path,
            removed_prefix_sha256=hashlib.sha256(b"").hexdigest(),
        )

    archive_text, result = build_archive_payload(
        history_path=history_path,
        original_lines=original_lines,
        keep_recent_lines=keep_recent_lines,
        archive_path=archive_path,
    )
    retained_lines = original_lines[-keep_recent_lines:]

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(archive_text, encoding="utf-8")
    history_path.write_text(
        build_recent_window(history_path=history_path, archive_path=archive_path, retained_lines=retained_lines),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Compact HISTORY.md into a recent-window surface")
    parser.add_argument("--history-path", default=str(DEFAULT_HISTORY_PATH))
    parser.add_argument("--archive-path", default=None)
    parser.add_argument("--keep-recent-lines", type=int, default=KEEP_RECENT_LINES)
    args = parser.parse_args()

    history_path = Path(args.history_path).resolve()
    archive_path = Path(args.archive_path).resolve() if args.archive_path else (history_path.parent / default_archive_path())
    result = compact_history(
        history_path=history_path,
        archive_path=archive_path,
        keep_recent_lines=args.keep_recent_lines,
    )
    print(
        "PASS compact-history "
        f"original_lines={result.original_lines} "
        f"archived_lines={result.archived_lines} "
        f"retained_lines={result.retained_lines} "
        f"archive_path={result.archive_path}"
    )


if __name__ == "__main__":
    main()
