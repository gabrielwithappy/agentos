"""
Read-only OKF v0.2 structural checker.

stdlib-only, no network access, no Git invocation, no file mutation.

Public API:
    validate_bundle(project_path: str, strict: bool = False) -> dict

Exit codes (returned via code field):
    0 - no errors (warnings allowed in non-strict mode)
    2 - structural error, refusal, or strict warning
    3 - filesystem error / unreadable path
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants and diagnostic codes
# ---------------------------------------------------------------------------

OKF_VERSION_SUPPORTED = "0.2"
MAX_FILE_BYTES = 1 * 1024 * 1024  # 1 MiB

# Structural error codes
CODE_ROOT_MISSING = "OKF_ROOT_MISSING"
CODE_INDEX_MISSING = "OKF_INDEX_MISSING"
CODE_LOG_MISSING = "OKF_LOG_MISSING"
CODE_VERSION_MISSING = "OKF_VERSION_MISSING"
CODE_VERSION_UNSUPPORTED = "OKF_VERSION_UNSUPPORTED"
CODE_FRONTMATTER_MISSING = "OKF_FRONTMATTER_MISSING"
CODE_FRONTMATTER_UNSUPPORTED = "OKF_FRONTMATTER_UNSUPPORTED"
CODE_TYPE_MISSING = "OKF_TYPE_MISSING"

# Refusal/filesystem error codes
CODE_PATH_SYMLINK = "OKF_PATH_SYMLINK"
CODE_FILE_BINARY = "OKF_FILE_BINARY"
CODE_FILE_OVERSIZE = "OKF_FILE_OVERSIZE"
CODE_FILE_UNREADABLE = "OKF_FILE_UNREADABLE"

# Advisory warning codes
CODE_DESCRIPTION_MISSING = "OKF_DESCRIPTION_MISSING"
CODE_STATUS_MALFORMED = "OKF_STATUS_MALFORMED"
CODE_TAGS_MALFORMED = "OKF_TAGS_MALFORMED"
CODE_SOURCES_MALFORMED = "OKF_SOURCES_MALFORMED"
CODE_GENERATED_MALFORMED = "OKF_GENERATED_MALFORMED"
CODE_VERIFIED_MALFORMED = "OKF_VERIFIED_MALFORMED"
CODE_STALE_AFTER_MALFORMED = "OKF_STALE_AFTER_MALFORMED"
CODE_LEGACY_TIMESTAMP = "OKF_LEGACY_TIMESTAMP"
CODE_LEGACY_CITATIONS = "OKF_LEGACY_CITATIONS"

VALID_STATUSES = {"draft", "stable", "deprecated"}

# Regex for advisory field validation
_RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_ACTOR_TS = re.compile(
    r"^(process|agent|human):[^@\s]+ @ \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
# slash-form tag: <prefix>/<non-empty-value>
_RE_TAG = re.compile(r"^[a-z][a-z0-9_-]*/[^\s/][^\s]*$")


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (flat subset only)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """
    Parse YAML frontmatter from Markdown text.

    Returns (fields_dict, error_code) where error_code is:
        None             - success
        CODE_FRONTMATTER_MISSING     - no opening ---
        CODE_FRONTMATTER_UNSUPPORTED - structural violation in the block
    """
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return None, CODE_FRONTMATTER_MISSING

    closing = None
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip() == "---":
            closing = i
            break
    if closing is None:
        return None, CODE_FRONTMATTER_UNSUPPORTED

    fm_lines = lines[1:closing]
    return _parse_flat_yaml(fm_lines)


def _parse_flat_yaml(lines: list[str]) -> tuple[dict[str, Any] | None, str | None]:
    """
    Parse a flat YAML subset:
    - key: scalar
    - key:
        - item1
        - item2

    Returns (dict, None) on success or (None, error_code) on parse error.
    Disallows: tabs, block scalars, anchors, tags, flow collections,
               nested mappings/lists, blank keys, duplicate keys.
    """
    result: dict[str, Any] = {}
    seen_keys: set[str] = set()
    i = 0

    while i < len(lines):
        raw = lines[i]

        # Disallow tabs
        if "\t" in raw:
            return None, CODE_FRONTMATTER_UNSUPPORTED

        stripped = raw.rstrip()

        # Skip blank lines
        if not stripped:
            i += 1
            continue

        # Anchor/tag/flow/block scalar markers
        if stripped.lstrip().startswith(("&", "*", "!", "|", ">")):
            return None, CODE_FRONTMATTER_UNSUPPORTED

        # Must be a key: value or key: (list follows)
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)', stripped)
        if not m:
            return None, CODE_FRONTMATTER_UNSUPPORTED

        key = m.group(1)
        val_raw = m.group(2).strip()

        if key in seen_keys:
            return None, CODE_FRONTMATTER_UNSUPPORTED  # duplicate key
        seen_keys.add(key)

        if val_raw == "":
            # Expect a list on subsequent lines
            items: list[str] = []
            i += 1
            while i < len(lines):
                item_line = lines[i]
                if "\t" in item_line:
                    return None, CODE_FRONTMATTER_UNSUPPORTED
                item_stripped = item_line.rstrip()
                if not item_stripped:
                    i += 1
                    continue
                item_m = re.match(r'^(\s*)-\s+(.*)', item_stripped)
                if not item_m:
                    # End of list (next key or end of block)
                    break
                item_val = item_m.group(2).strip()
                # Disallow nested mapping/list items
                if item_val.startswith(("{", "[")):
                    return None, CODE_FRONTMATTER_UNSUPPORTED
                items.append(_unquote(item_val))
                i += 1
            result[key] = items
        else:
            # Scalar value — disallow flow collections
            if val_raw.startswith(("{", "[")):
                return None, CODE_FRONTMATTER_UNSUPPORTED
            result[key] = _unquote(val_raw)
            i += 1

    return result, None


def _unquote(s: str) -> str:
    """Remove surrounding single or double quotes from a scalar."""
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s


# ---------------------------------------------------------------------------
# File reading helpers
# ---------------------------------------------------------------------------

def _read_file_safe(path: Path) -> tuple[str | None, str | None]:
    """
    Read a file safely. Returns (content, None) or (None, error_code).
    Refuses symlinks, binary files, files > 1 MiB.
    """
    if path.is_symlink():
        return None, CODE_PATH_SYMLINK
    try:
        size = path.stat().st_size
    except OSError:
        return None, CODE_FILE_UNREADABLE
    if size > MAX_FILE_BYTES:
        return None, CODE_FILE_OVERSIZE
    try:
        content = path.read_bytes()
    except OSError:
        return None, CODE_FILE_UNREADABLE
    if b"\x00" in content:
        return None, CODE_FILE_BINARY
    try:
        return content.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, CODE_FILE_BINARY


# ---------------------------------------------------------------------------
# Next-action messages for each code
# ---------------------------------------------------------------------------

_NEXT_MESSAGES: dict[str, str] = {
    CODE_ROOT_MISSING: "Run init --okf-starter or create the bundle root directory.",
    CODE_INDEX_MISSING: "Create index.md with okf_version: \"0.2\" frontmatter.",
    CODE_LOG_MISSING: "Create log.md to record activity.",
    CODE_VERSION_MISSING: "Add okf_version: \"0.2\" to index.md frontmatter.",
    CODE_VERSION_UNSUPPORTED: "Update okf_version in index.md to \"0.2\".",
    CODE_FRONTMATTER_MISSING: "Add a YAML frontmatter block (--- ... ---) to the file.",
    CODE_FRONTMATTER_UNSUPPORTED: "Simplify frontmatter to flat key: scalar or key:\\n  - item list; remove tabs, anchors, flow collections, and nested mappings.",
    CODE_TYPE_MISSING: "Add a non-empty 'type:' field to the concept frontmatter.",
    CODE_PATH_SYMLINK: "Replace the symlink with a real UTF-8 Markdown file.",
    CODE_FILE_BINARY: "Replace the binary file with a real UTF-8 Markdown file.",
    CODE_FILE_OVERSIZE: "Split or trim the file to under 1 MiB.",
    CODE_FILE_UNREADABLE: "Correct filesystem permissions and retry validate.",
    CODE_DESCRIPTION_MISSING: "Add a non-empty 'description:' field to the frontmatter.",
    CODE_STATUS_MALFORMED: "Set 'status:' to one of: draft, stable, deprecated.",
    CODE_TAGS_MALFORMED: "Set 'tags:' to a list of slash-form strings (e.g. action/plan, domain/knowledge-curator).",
    CODE_SOURCES_MALFORMED: "Set 'sources:' to a plain scalar or a list of plain scalars.",
    CODE_GENERATED_MALFORMED: "Set 'generated:' to 'process:<id>|agent:<id>|human:<id> @ YYYY-MM-DDTHH:MM:SSZ'.",
    CODE_VERIFIED_MALFORMED: "Set 'verified:' to the same actor/timestamp scalar or a list of such scalars.",
    CODE_STALE_AFTER_MALFORMED: "Set 'stale_after:' to a date in YYYY-MM-DD format.",
    CODE_LEGACY_TIMESTAMP: "Remove the legacy 'timestamp:' field; use 'log.md' for activity records.",
    CODE_LEGACY_CITATIONS: "Remove '# Citations' sections; record sources in 'sources:' frontmatter.",
}

_STRICT_NEXT = "Add or correct the advisory metadata, or re-run validate without --strict."


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def _diag(path_str: str, severity: str, code: str) -> dict[str, str]:
    return {
        "path": path_str,
        "severity": severity,
        "code": code,
        "message": _NEXT_MESSAGES.get(code, code),
    }


def _sort_key(d: dict[str, str]) -> tuple[str, int, str]:
    sev_order = {"error": 0, "warning": 1}
    return (d["path"], sev_order.get(d["severity"], 2), d["code"])


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def _check_index(root: Path, diagnostics: list[dict]) -> None:
    """Check index.md for presence and okf_version."""
    index_path = root / "index.md"
    if not index_path.exists():
        diagnostics.append(_diag("index.md", "error", CODE_INDEX_MISSING))
        return

    content, err = _read_file_safe(index_path)
    if err:
        diagnostics.append(_diag("index.md", "error", err))
        return

    assert content is not None
    fields, parse_err = _parse_frontmatter(content)
    if parse_err:
        diagnostics.append(_diag("index.md", "error", parse_err))
        return

    assert fields is not None
    version = fields.get("okf_version")
    if not version:
        diagnostics.append(_diag("index.md", "error", CODE_VERSION_MISSING))
    elif str(version).strip() != OKF_VERSION_SUPPORTED:
        diagnostics.append(_diag("index.md", "error", CODE_VERSION_UNSUPPORTED))


def _check_log(root: Path, diagnostics: list[dict]) -> None:
    """Check log.md for presence."""
    log_path = root / "log.md"
    if not log_path.exists():
        diagnostics.append(_diag("log.md", "error", CODE_LOG_MISSING))
        return
    content, err = _read_file_safe(log_path)
    if err:
        diagnostics.append(_diag("log.md", "error", err))


def _check_advisory(rel_path: str, fields: dict[str, Any], diagnostics: list[dict]) -> None:
    """Check advisory fields for a concept file."""
    # description
    desc = fields.get("description")
    if not desc or (isinstance(desc, str) and not desc.strip()):
        diagnostics.append(_diag(rel_path, "warning", CODE_DESCRIPTION_MISSING))

    # status
    status = fields.get("status")
    if status is not None and str(status).strip() not in VALID_STATUSES:
        diagnostics.append(_diag(rel_path, "warning", CODE_STATUS_MALFORMED))

    # tags
    tags = fields.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not tags:
            diagnostics.append(_diag(rel_path, "warning", CODE_TAGS_MALFORMED))
        else:
            for tag in tags:
                if not isinstance(tag, str) or not _RE_TAG.match(tag):
                    diagnostics.append(_diag(rel_path, "warning", CODE_TAGS_MALFORMED))
                    break

    # sources
    sources = fields.get("sources")
    if sources is not None:
        if isinstance(sources, list):
            if not sources or not all(isinstance(s, str) and s.strip() for s in sources):
                diagnostics.append(_diag(rel_path, "warning", CODE_SOURCES_MALFORMED))
        elif not isinstance(sources, str) or not sources.strip():
            diagnostics.append(_diag(rel_path, "warning", CODE_SOURCES_MALFORMED))

    # generated
    generated = fields.get("generated")
    if generated is not None:
        if not isinstance(generated, str) or not _RE_ACTOR_TS.match(generated.strip()):
            diagnostics.append(_diag(rel_path, "warning", CODE_GENERATED_MALFORMED))

    # verified
    verified = fields.get("verified")
    if verified is not None:
        if isinstance(verified, list):
            if not verified or not all(isinstance(v, str) and _RE_ACTOR_TS.match(v.strip()) for v in verified):
                diagnostics.append(_diag(rel_path, "warning", CODE_VERIFIED_MALFORMED))
        elif not isinstance(verified, str) or not _RE_ACTOR_TS.match(verified.strip()):
            diagnostics.append(_diag(rel_path, "warning", CODE_VERIFIED_MALFORMED))

    # stale_after
    stale_after = fields.get("stale_after")
    if stale_after is not None:
        if not isinstance(stale_after, str) or not _RE_DATE.match(stale_after.strip()):
            diagnostics.append(_diag(rel_path, "warning", CODE_STALE_AFTER_MALFORMED))

    # legacy timestamp
    if "timestamp" in fields:
        diagnostics.append(_diag(rel_path, "warning", CODE_LEGACY_TIMESTAMP))


def _check_legacy_citations(rel_path: str, content: str, diagnostics: list[dict]) -> None:
    """Check for legacy '# Citations' sections."""
    for line in content.splitlines():
        if re.match(r"^#{1,6}\s+Citations\s*$", line):
            diagnostics.append(_diag(rel_path, "warning", CODE_LEGACY_CITATIONS))
            break


def _check_concept(root: Path, rel_path: str, diagnostics: list[dict]) -> None:
    """Check a single concept file."""
    path = root / rel_path
    if path.is_symlink():
        diagnostics.append(_diag(rel_path, "error", CODE_PATH_SYMLINK))
        return

    content, err = _read_file_safe(path)
    if err:
        diagnostics.append(_diag(rel_path, "error", err))
        return

    assert content is not None
    fields, parse_err = _parse_frontmatter(content)
    if parse_err == CODE_FRONTMATTER_MISSING:
        diagnostics.append(_diag(rel_path, "error", CODE_FRONTMATTER_MISSING))
        return
    if parse_err:
        diagnostics.append(_diag(rel_path, "error", parse_err))
        return

    assert fields is not None
    concept_type = fields.get("type")
    if not concept_type or (isinstance(concept_type, str) and not concept_type.strip()):
        diagnostics.append(_diag(rel_path, "error", CODE_TYPE_MISSING))

    _check_advisory(rel_path, fields, diagnostics)
    _check_legacy_citations(rel_path, content, diagnostics)


def _discover_concepts(root: Path) -> list[str]:
    """
    Discover concept files: *.md files in subdirectories of root.
    Skips: index.md, log.md (reserved), symlinks, directories.
    """
    concepts: list[str] = []
    reserved_top = {"index.md", "log.md"}

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        # Skip symlink directories
        if current.is_symlink():
            continue
        # Skip the root level's reserved files
        rel_dir = current.relative_to(root)
        if str(rel_dir) == ".":
            # Top-level: skip reserved
            for fname in filenames:
                if fname not in reserved_top and fname.endswith(".md"):
                    rel = fname
                    concepts.append(rel)
        else:
            for fname in filenames:
                if fname.endswith(".md"):
                    rel = str(Path(rel_dir) / fname)
                    concepts.append(rel)

    return sorted(concepts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_bundle(project_path: str, strict: bool = False) -> dict[str, Any]:
    """
    Validate an OKF v0.2 bundle at the given path.

    Returns a single result dict with:
        ok: bool
        code: 0 | 2 | 3
        action: "validate"
        changed: false
        diagnostics: list of {path, severity, code, message}
        next: str
    """
    root = Path(project_path).resolve()
    diagnostics: list[dict] = []

    # Check root
    if root.is_symlink():
        d = _diag(str(root), "error", CODE_PATH_SYMLINK)
        return _envelope(False, 3, diagnostics=[d], next_msg=_NEXT_MESSAGES[CODE_PATH_SYMLINK])

    if not root.exists() or not root.is_dir():
        d = _diag(str(root), "error", CODE_ROOT_MISSING)
        return _envelope(False, 2, diagnostics=[d], next_msg=_NEXT_MESSAGES[CODE_ROOT_MISSING])

    # Check required files
    _check_index(root, diagnostics)
    _check_log(root, diagnostics)

    # Check concepts
    try:
        concepts = _discover_concepts(root)
    except OSError as exc:
        d = _diag(str(root), "error", CODE_FILE_UNREADABLE)
        d["message"] = f"Directory traversal failed: {exc}"
        return _envelope(False, 3, diagnostics=[d], next_msg=_NEXT_MESSAGES[CODE_FILE_UNREADABLE])

    for rel in concepts:
        _check_concept(root, rel, diagnostics)

    # Deduplicate: same (path, code) → keep first
    seen: set[tuple[str, str]] = set()
    unique_diags: list[dict] = []
    for d in diagnostics:
        key = (d["path"], d["code"])
        if key not in seen:
            seen.add(key)
            unique_diags.append(d)

    # Sort: path lex → severity (error before warning) → code lex
    unique_diags.sort(key=_sort_key)

    has_errors = any(d["severity"] == "error" for d in unique_diags)
    has_warnings = any(d["severity"] == "warning" for d in unique_diags)

    if has_errors:
        code = 2
        ok = False
        next_msg = "Fix the reported errors and re-run validate."
    elif strict and has_warnings:
        code = 2
        ok = False
        next_msg = "Add or correct the advisory metadata, or re-run validate without --strict."
    else:
        code = 0
        ok = True
        if has_warnings:
            next_msg = "Advisory warnings found. Run validate --strict to enforce them, or improve the metadata."
        else:
            next_msg = "OKF v0.2 bundle is valid."

    return _envelope(ok, code, diagnostics=unique_diags, next_msg=next_msg)


def _envelope(ok: bool, code: int, diagnostics: list[dict], next_msg: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "code": code,
        "action": "validate",
        "changed": False,
        "diagnostics": diagnostics,
        "next": next_msg,
    }
