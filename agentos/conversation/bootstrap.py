from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from agentos.conversation.threat_patterns import scan_for_threats
from agentos.conversation.types import TRUSTED_SYSTEM_SOURCE, ConversationMessage, ConversationState, new_message_id
from agentos.llm.redaction import redact_text

CONTEXT_FILENAMES = ("AGENTS.md", "AGENTS.MD", "CLAUDE.md", "CLAUDE.MD")
CORE_KNOWLEDGE_PATHS = (
    ".agents/AGENTS.md",
    "HISTORY.md",
    ".agents/skills/harness/brain/lessons-learned.md",
    ".agents/vendors/codex.md",
    ".agents/vendors/claude.md",
    ".agents/vendors/gemini.md",
)

SKIP_ENV_VAR = "AGENTOS_SKIP_CONTEXT_BOOTSTRAP"

# Fixed floor from hermes-agent's `_dynamic_context_file_max_chars()`. This
# plan starts with the fixed floor only — proportional scaling against a
# model's context window is deferred until the registry exposes
# `context_length` (see plan's '이번 범위에 포함하지 않는 것').
MAX_CONTEXT_FILE_CHARS = 20_000
_TRUNCATION_HEAD_CHARS = 12_000
_TRUNCATION_TAIL_CHARS = 6_000

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
_FRONTMATTER_FIELD_RE = re.compile(r"^(name|description)\s*:\s*(.+)$")

# A line that is *only* `@<path>` (optionally trailing whitespace) is an
# include directive, matching Claude Code's `CLAUDE.md` `@path` syntax. The
# path itself must not contain whitespace, so a line like "@see the docs"
# (prose, not a reference) is never misread as an include.
_INCLUDE_LINE_RE = re.compile(r"^@(\S+)\s*$")

# Recursion guard: unrelated to MAX_CONTEXT_FILE_CHARS/MAX_SCAN_CHARS, which
# cap the *assembled* text — this caps include depth before that text even
# exists, so a long include chain can't hang expansion itself.
MAX_INCLUDE_DEPTH = 5


@dataclass(frozen=True)
class ContextFile:
    """One discovered `AGENTS.md`/`CLAUDE.md` candidate.

    `skipped` distinguishes "found but unreadable" (permission error, bad
    encoding, broken symlink) from "not found at all" — callers use this to
    report a skip count without treating a missing file as an error.

    `blocked` is distinct from `skipped`: a skip means the file couldn't be
    read; a block means it was read fine but its content matched a threat
    pattern, so its content was replaced before being handed to the LLM.
    `truncated` marks files that were read fine but exceeded
    `MAX_CONTEXT_FILE_CHARS` and had their middle cut.
    """

    path: Path
    content: str
    skipped: bool = False
    skip_reason: str | None = None
    blocked: bool = False
    blocked_reasons: tuple[str, ...] = ()
    truncated: bool = False


@dataclass(frozen=True)
class SkillMeta:
    """Metadata-only view of an installed skill: never the full `SKILL.md`
    body, matching pi's lazy-loading pattern (`formatSkillsForPrompt`)."""

    name: str
    description: str
    path: Path
    skipped: bool = False
    skip_reason: str | None = None


def _read_file_safely(path: Path) -> tuple[str | None, str | None]:
    """Returns `(content, None)` on success or `(None, reason)` on any
    read failure (permission, encoding, broken symlink) — never raises."""
    try:
        return path.read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, str(exc)
    except UnicodeDecodeError as exc:
        return None, f"encoding error: {exc}"


def _find_context_file_in_dir(directory: Path) -> ContextFile | None:
    for filename in CONTEXT_FILENAMES:
        candidate = directory / filename
        if not candidate.is_file():
            continue
        content, error = _read_file_safely(candidate)
        if error is not None:
            return ContextFile(path=candidate, content="", skipped=True, skip_reason=error)
        assert content is not None
        expanded = _expand_includes(
            content,
            current_file=candidate,
            trusted_roots=(directory,),
            visited={candidate},
        )
        return ContextFile(path=candidate, content=expanded)
    return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _expand_includes(
    content: str,
    *,
    current_file: Path,
    trusted_roots: tuple[Path, ...],
    visited: set[Path],
    depth: int = 0,
) -> str:
    """Recursively replaces `@<path>` lines with the referenced file's
    content, matching Claude Code's `CLAUDE.md` include syntax.

    Relative `@<path>` references are resolved against `current_file`'s
    directory. An include is only honored when the resolved path lands
    inside one of `trusted_roots` — the directory the *including* context
    file itself was discovered in (never an ancestor of it) — so an
    `AGENTS.md` found while walking untrusted ancestor directories can only
    pull in files at or below its own location, never reach up to `~/.ssh`
    or sideways into an unrelated tree. This is narrower than Claude Code's
    own `@~/anything` support, chosen deliberately: a context file
    discovered via ancestor-directory walking is exactly the untrusted
    input this plan's threat model targets. Anything else — an escape
    attempt, a missing file, a circular reference, or hitting
    `MAX_INCLUDE_DEPTH` — is replaced with an inline
    `[INCLUDE_BLOCKED: ...]`/`[INCLUDE_SKIPPED: ...]` marker rather than
    raising, so one bad include never aborts the whole bootstrap.
    """
    lines = content.splitlines(keepends=True)
    expanded: list[str] = []
    for line in lines:
        stripped = line.rstrip("\r\n")
        line_ending = line[len(stripped):]
        match = _INCLUDE_LINE_RE.match(stripped)
        if match is None:
            expanded.append(line)
            continue

        raw_ref = match.group(1)
        if depth + 1 >= MAX_INCLUDE_DEPTH:
            expanded.append(f"[INCLUDE_BLOCKED: @{raw_ref} exceeds max include depth {MAX_INCLUDE_DEPTH}]{line_ending}")
            continue
        referenced = Path(raw_ref).expanduser()
        if not referenced.is_absolute():
            referenced = current_file.parent / referenced
        try:
            resolved = referenced.resolve()
        except OSError:
            expanded.append(f"[INCLUDE_BLOCKED: @{raw_ref} could not be resolved]{line_ending}")
            continue

        if not any(_is_within(resolved, root) for root in trusted_roots):
            expanded.append(f"[INCLUDE_BLOCKED: @{raw_ref} escapes trusted context root]{line_ending}")
            continue

        if resolved in visited:
            expanded.append(f"[INCLUDE_SKIPPED: @{raw_ref} already included (circular reference)]{line_ending}")
            continue

        include_content, error = _read_file_safely(resolved)
        if error is not None:
            expanded.append(f"[INCLUDE_BLOCKED: @{raw_ref} could not be read ({error})]{line_ending}")
            continue

        assert include_content is not None
        nested = _expand_includes(
            include_content,
            current_file=resolved,
            trusted_roots=trusted_roots,
            visited=visited | {resolved},
            depth=depth + 1,
        )
        if not nested.endswith("\n"):
            nested += "\n"
        expanded.append(nested)

    return "".join(expanded)


def discover_context_files(cwd: str | Path, agent_home: str | Path | None = None) -> list[ContextFile]:
    """Walks `cwd` up to the filesystem root looking for one context file per
    directory (first of `CONTEXT_FILENAMES` wins), plus one global candidate
    under `agent_home` if given. Order: global first, then ancestors from
    the filesystem root down to `cwd` (closest directory last), matching
    pi's `loadProjectContextFiles` ordering so the most locally-relevant
    instructions land last in the assembled message.

    Unreadable files (permission error, bad encoding, broken symlink) are
    still returned with `skipped=True` so callers can report a skip count;
    they are never raised as exceptions and never block discovery of other
    files.
    """
    resolved_cwd = Path(cwd).resolve()
    results: list[ContextFile] = []
    seen_paths: set[Path] = set()

    if agent_home is not None:
        global_dir = Path(agent_home).resolve()
        global_file = _find_context_file_in_dir(global_dir)
        if global_file is not None:
            results.append(global_file)
            seen_paths.add(global_file.path)

    ancestors: list[ContextFile] = []
    current_dir = resolved_cwd
    while True:
        found = _find_context_file_in_dir(current_dir)
        if found is not None and found.path not in seen_paths:
            ancestors.append(found)
            seen_paths.add(found.path)
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break
        current_dir = parent_dir

    ancestors.reverse()
    results.extend(ancestors)
    # A repository's root AGENTS.md defines mandatory operating knowledge.
    # Load the bounded, versioned knowledge graph explicitly rather than
    # following arbitrary prose links from untrusted project context files.
    project_root = next((item.path.parent for item in results if item.path.name.lower() == "agents.md"), None)
    if project_root is not None:
        for relative in CORE_KNOWLEDGE_PATHS:
            candidate = project_root / relative
            if candidate in seen_paths or candidate.is_symlink() or not candidate.is_file():
                continue
            content, error = _read_file_safely(candidate)
            if error is not None:
                results.append(ContextFile(path=candidate, content="", skipped=True, skip_reason=error))
            else:
                results.append(ContextFile(path=candidate, content=content or ""))
            seen_paths.add(candidate)
    return results


def _parse_skill_frontmatter(content: str) -> tuple[str | None, str | None]:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None, None
    name: str | None = None
    description: str | None = None
    for line in match.group(1).splitlines():
        field_match = _FRONTMATTER_FIELD_RE.match(line.strip())
        if not field_match:
            continue
        key, value = field_match.group(1), field_match.group(2).strip()
        if key == "name":
            name = value
        elif key == "description":
            description = value
    return name, description


def _first_body_line(content: str) -> str:
    without_frontmatter = _FRONTMATTER_RE.sub("", content, count=1)
    for line in without_frontmatter.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return ""


def discover_skills(skills_dir: str | Path | Iterable[str | Path]) -> list[SkillMeta]:
    """Scans `skills_dir` for `<skill-name>/SKILL.md` entries and parses
    only their name/description frontmatter — never the full skill body,
    matching pi's metadata-only exposure (`formatSkillsForPrompt`)."""
    results: list[SkillMeta] = []
    directories = (Path(skills_dir),) if isinstance(skills_dir, (str, Path)) else tuple(Path(item) for item in skills_dir)
    seen_names: set[str] = set()
    for directory in directories:
        if not directory.is_dir() or directory.is_symlink():
            continue
        for entry in sorted(directory.iterdir()):
            if entry.name in seen_names or not entry.is_dir() or entry.is_symlink():
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.is_symlink() or not skill_file.is_file():
                continue
            seen_names.add(entry.name)
            content, error = _read_file_safely(skill_file)
            if error is not None:
                results.append(SkillMeta(name=entry.name, description="", path=skill_file, skipped=True, skip_reason=error))
                continue
            assert content is not None
            name, description = _parse_skill_frontmatter(content)
            results.append(SkillMeta(name=name or entry.name, description=description or _first_body_line(content), path=skill_file))
    return results


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate_content(content: str, path: Path) -> str:
    """Keeps only the head and tail of `content`, inserting a marker that
    points back to `path` for readers who need the full text. Mirrors
    hermes-agent's `_truncate_content` head/tail shape."""
    total = len(content)
    head = content[:_TRUNCATION_HEAD_CHARS]
    tail = content[-_TRUNCATION_TAIL_CHARS:]
    marker = (
        f"\n[...truncated {path.name}: kept {len(head)}+{len(tail)} of {total} chars. "
        f"See full file at: {path}]\n"
    )
    return head + marker + tail


def scan_and_cap_context_file(context_file: ContextFile) -> ContextFile:
    """Runs threat scanning and size capping on one already-read
    `ContextFile`, returning a new `ContextFile` with `content`/`blocked`/
    `blocked_reasons`/`truncated` updated. Skipped files pass through
    unchanged. Scanning happens on the raw content, before `redact_text()`
    is applied by the caller."""
    if context_file.skipped:
        return context_file

    findings = scan_for_threats(context_file.content, scope="context")
    if findings:
        blocked_text = (
            f"[BLOCKED: {context_file.path.name} contained potential prompt "
            f"injection ({', '.join(findings)}). Content not loaded.]"
        )
        return ContextFile(
            path=context_file.path,
            content=blocked_text,
            blocked=True,
            blocked_reasons=tuple(findings),
        )

    if len(context_file.content) > MAX_CONTEXT_FILE_CHARS:
        return ContextFile(
            path=context_file.path,
            content=_truncate_content(context_file.content, context_file.path),
            truncated=True,
        )

    return context_file


def build_bootstrap_message(
    context_files: list[ContextFile], skills: list[SkillMeta]
) -> ConversationMessage | None:
    """Assembles discovered context files/skills into one trusted `system`
    message using pi's `<project_context>`/`<available_skills>` XML shape.
    Returns `None` when nothing usable was found so new sessions don't
    carry an empty system message.

    Each context file is scanned for prompt-injection patterns and capped
    to `MAX_CONTEXT_FILE_CHARS` before `redact_text()` is applied — see
    `scan_and_cap_context_file()`."""
    usable_files = [
        scan_and_cap_context_file(f) for f in context_files if not f.skipped
    ]
    usable_skills = [s for s in skills if not s.skipped]

    if not usable_files and not usable_skills:
        return None

    parts: list[str] = []

    if usable_files:
        parts.append("<project_context>\n\nProject-specific instructions and guidelines:\n")
        for context_file in usable_files:
            sanitized = redact_text(context_file.content)
            parts.append(
                f'<project_instructions path="{_escape_xml(str(context_file.path))}">\n'
                f"{sanitized}\n</project_instructions>\n"
            )
        parts.append("</project_context>")

    if usable_skills:
        parts.append(
            "\nThe following skills provide specialized instructions for specific tasks.\n"
            "Use the read tool to load a skill's file when the task matches its description.\n"
            "<available_skills>"
        )
        for skill in usable_skills:
            parts.append(
                "  <skill>\n"
                f"    <name>{_escape_xml(skill.name)}</name>\n"
                f"    <description>{_escape_xml(skill.description)}</description>\n"
                f"    <location>{_escape_xml(str(skill.path))}</location>\n"
                "  </skill>"
            )
        parts.append("</available_skills>")

    text = "\n".join(parts)
    return ConversationMessage(
        id=new_message_id(),
        role="system",
        text=text,
        source=TRUSTED_SYSTEM_SOURCE,
        metadata={
            "bootstrap_context_paths": [str(f.path) for f in usable_files],
            "bootstrap_skill_names": [s.name for s in usable_skills],
            "bootstrap_blocked_files": [
                {"path": str(f.path), "reasons": list(f.blocked_reasons)}
                for f in usable_files
                if f.blocked
            ],
            "bootstrap_truncated_files": [str(f.path) for f in usable_files if f.truncated],
        },
    )


def build_bootstrap_message_for_session(
    cwd: str | Path, agent_home: str | Path | None, skills_dir: str | Path | Iterable[str | Path]
) -> tuple[ConversationMessage | None, int, int, int]:
    """Top-level entry point used by session creation: honors
    `AGENTOS_SKIP_CONTEXT_BOOTSTRAP` so callers never need to know about the
    opt-out env var themselves. Returns `(message, loaded_file_count,
    loaded_skill_count, skipped_count)` for banner/status reporting."""
    if os.environ.get(SKIP_ENV_VAR, "").strip() not in ("", "0", "false", "False"):
        return None, 0, 0, 0

    context_files = discover_context_files(cwd, agent_home)
    skills = discover_skills(skills_dir)

    loaded_files = sum(1 for f in context_files if not f.skipped)
    loaded_skills = sum(1 for s in skills if not s.skipped)
    skipped_count = sum(1 for f in context_files if f.skipped) + sum(1 for s in skills if s.skipped)

    message = build_bootstrap_message(context_files, skills)
    return message, loaded_files, loaded_skills, skipped_count


def find_bootstrap_message(state: ConversationState, branch_id: str | None = None) -> ConversationMessage | None:
    """Finds the trusted bootstrap system message already committed to
    `state`, if any — used by `/status`/banner code to describe what was
    loaded without re-reading the filesystem or re-parsing the assembled
    XML text."""
    resolved_branch = branch_id or state.active_branch_id
    for message in state.branch_messages(resolved_branch):
        if message.is_trusted_system():
            return message
    return None
