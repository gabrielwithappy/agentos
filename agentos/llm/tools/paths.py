from __future__ import annotations

from pathlib import Path

# Shared containment boundary for every tool that touches the filesystem.
# It lives in exactly one place on purpose: each tool re-implementing this
# check would only need to get it wrong once to open an escape route.


def resolve_within_cwd(
    path: str,
    cwd: Path,
    allowed_paths: tuple[Path, ...] = (),
    blocked_roots: tuple[Path, ...] = (),
) -> Path | None:
    """Resolves `path` against `cwd` and returns it only if the fully
    resolved path (symlinks included) lands inside `cwd`. Resolution happens
    before the containment check — checking first would let a symlink whose
    target lives outside `cwd` slip through undetected."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    resolved = candidate.resolve()
    resolved_cwd = cwd.resolve()
    resolved_allowed = tuple(entry.resolve() for entry in allowed_paths)
    if resolved in resolved_allowed:
        return resolved
    if any(resolved.is_relative_to(root.resolve()) for root in blocked_roots):
        return None
    if not resolved.is_relative_to(resolved_cwd):
        return None
    return resolved


def truncate_output(text: str, max_bytes: int) -> tuple[str, bool]:
    """Caps `text` at `max_bytes` of UTF-8, returning `(text, truncated)`.
    Decoding with `errors="ignore"` so a cut through a multi-byte character
    drops that character rather than raising."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, False
    return encoded[:max_bytes].decode("utf-8", errors="ignore"), True


__all__ = ["resolve_within_cwd", "truncate_output"]
