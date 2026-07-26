"""Threat-pattern library for context file (`AGENTS.md`/`CLAUDE.md`) scanning.

Ported from hermes-agent's `tools/threat_patterns.py`, scoped down to the
`"all"`/`"context"` patterns only — this module does not implement hermes'
`"strict"` scope (SSH backdoor paths, hardcoded secrets, memory/skill-install
checks), which targets features AgentOS does not have yet. See
`.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`
for the full comparison.

This is an advisory, best-effort mitigation, not a guarantee — a
sufficiently obfuscated payload can still slip past regex matching.
"""

from __future__ import annotations

import re
import unicodedata

# Hard cap on text scanned with regexes. Context files can be arbitrarily
# large, and this scanner is an advisory guard rather than archival search;
# bounding input keeps worst-case runtime predictable.
MAX_SCAN_CHARS = 65_536

# Bounded filler between key attack words — unbounded `(?:\w+\s+)*` can
# backtrack heavily on adversarial near-misses, so cap it at 8 words.
_FILLER = r"(?:\w+\s+){0,8}"

# Each entry: (regex, pattern_id, scope). scope in {"all", "context"}.
_PATTERNS: list[tuple[str, str, str]] = [
    # ── Classic prompt injection (applies everywhere) ────────────────
    (rf"ignore\s+{_FILLER}(previous|all|above|prior)\s+{_FILLER}instructions", "prompt_injection", "all"),
    (r"system\s+prompt\s+override", "sys_prompt_override", "all"),
    (rf"disregard\s+{_FILLER}(your|all|any)\s+{_FILLER}(instructions|rules|guidelines)", "disregard_rules", "all"),
    (rf"act\s+as\s+(if|though)\s+{_FILLER}you\s+{_FILLER}(have\s+no|don't\s+have)\s+{_FILLER}(restrictions|limits|rules)", "bypass_restrictions", "all"),
    (r"<!--[^>]{0,512}(?:ignore|override|system|secret|hidden)[^>]{0,512}-->", "html_comment_injection", "all"),
    (r"<\s*div\s+style\s*=\s*[\"'][^>]{0,2048}display\s*:\s*none", "hidden_div", "all"),
    (r"translate\s+[^\n]{0,512}\s+into\s+[^\n]{0,512}\s+and\s+(execute|run|eval)", "translate_execute", "all"),
    (rf"do\s+not\s+{_FILLER}tell\s+{_FILLER}the\s+user", "deception_hide", "all"),

    # ── Role-play / identity hijack (context scope) ──────────────────
    (rf"you\s+are\s+{_FILLER}now\s+(?:a|an|the)\s+", "role_hijack", "context"),
    (rf"pretend\s+{_FILLER}(you\s+are|to\s+be)\s+", "role_pretend", "context"),
    (rf"output\s+{_FILLER}(system|initial)\s+prompt", "leak_system_prompt", "context"),
    (rf"(respond|answer|reply)\s+without\s+{_FILLER}(restrictions|limitations|filters|safety)", "remove_filters", "context"),
    (rf"you\s+have\s+been\s+{_FILLER}(updated|upgraded|patched)\s+to", "fake_update", "context"),
    (r"\bname\s+yourself\s+\w+", "identity_override", "context"),

    # ── C2 / promptware behavior (context scope) ──────────────────────
    (r"register\s+(as\s+)?a?\s*node", "c2_node_registration", "context"),
    (r"(heartbeat|beacon|check[\s\-]?in)\s+(to|with)\s+", "c2_heartbeat", "context"),
    (r"pull\s+(down\s+)?(?:new\s+)?task(?:ing|s)?\b", "c2_task_pull", "context"),
    (r"connect\s+to\s+the\s+network\b", "c2_network_connect", "context"),
    (r"you\s+must\s+(?:\w+\s+){0,3}(register|connect|report|beacon)\b", "forced_action", "context"),
    (r"only\s+use\s+one[\s\-]?liners?\b", "anti_forensic_oneliner", "context"),
    (rf"never\s+{_FILLER}(?:create|write)\s+{_FILLER}(?:script|file)\s+{_FILLER}disk", "anti_forensic_disk", "context"),
    (r"unset\s+\w*(?:CLAUDE|CODEX|HERMES|AGENT|OPENAI|ANTHROPIC)\w*", "env_var_unset_agent", "context"),

    # ── Known C2 / red-team framework names (context scope) ──────────
    (r"\b(?:cobalt\s*strike|sliver|havoc|mythic|metasploit|brainworm)\b", "known_c2_framework", "context"),
    (r"\bc2\s+(?:server|channel|infrastructure|beacon)\b", "c2_explicit", "context"),
    (r"\bcommand\s+and\s+control\b", "c2_explicit_long", "context"),

    # ── Exfiltration via curl/wget/cat with secrets (applies everywhere) ──
    (r"curl\s+[^\n]{0,2048}\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)", "exfil_curl", "all"),
    (r"wget\s+[^\n]{0,2048}\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)", "exfil_wget", "all"),
    (r"cat\s+[^\n]{0,2048}(\.env|credentials|\.netrc|\.pgpass|\.npmrc|\.pypirc)", "read_secrets", "all"),
]

# Invisible / bidirectional unicode characters used in injection attacks.
INVISIBLE_CHARS = frozenset({
    "​",  # zero-width space
    "‌",  # zero-width non-joiner
    "‍",  # zero-width joiner
    "⁠",  # word joiner
    "⁢",  # invisible times
    "⁣",  # invisible separator
    "⁤",  # invisible plus
    "﻿",  # zero-width no-break space (BOM)
    "‪",  # left-to-right embedding
    "‫",  # right-to-left embedding
    "‬",  # pop directional formatting
    "‭",  # left-to-right override
    "‮",  # right-to-left override
    "⁦",  # left-to-right isolate
    "⁧",  # right-to-left isolate
    "⁨",  # first strong isolate
    "⁩",  # pop directional isolate
})

_COMPILED: dict[str, list[tuple[re.Pattern, str]]] = {}


def _compile() -> None:
    """Compile pattern sets per scope. `"all"` patterns land in both sets;
    `"context"` patterns land in `"context"` only."""
    global _COMPILED
    if _COMPILED:
        return

    all_patterns: list[tuple[re.Pattern, str]] = []
    context_patterns: list[tuple[re.Pattern, str]] = []

    for pattern, pid, scope in _PATTERNS:
        compiled = re.compile(pattern, re.IGNORECASE)
        entry = (compiled, pid)
        if scope == "all":
            all_patterns.append(entry)
            context_patterns.append(entry)
        elif scope == "context":
            context_patterns.append(entry)
        else:
            raise ValueError(f"threat_patterns: unknown scope {scope!r} for pattern {pid!r}")

    _COMPILED = {
        "all": all_patterns,
        "context": context_patterns,
    }


_compile()


def scan_for_threats(content: str, scope: str = "context") -> list[str]:
    """Return matched pattern IDs in `content` at the given scope.

    `scope="all"`: classic injection + exfil only.
    `scope="context"` (default): adds promptware / C2 / role-play patterns,
    suitable for `AGENTS.md`/`CLAUDE.md` context files.

    Also detects invisible unicode characters, returned as
    `"invisible_unicode_U+XXXX"`.
    """
    if not content:
        return []

    findings: list[str] = []

    content = content[:MAX_SCAN_CHARS]

    # Invisible unicode — checked on raw content before NFKC normalization,
    # since normalization can strip some of these codepoints.
    char_set = set(content)
    invisible_hits = char_set & INVISIBLE_CHARS
    for ch in invisible_hits:
        findings.append(f"invisible_unicode_U+{ord(ch):04X}")

    # NFKC folds full-width/compatibility unicode variants (e.g. ｃａｔ → cat)
    # to ASCII before the regex engine sees them, preventing homograph
    # bypass of keyword checks. Does not defend against cross-script
    # confusables (e.g. Cyrillic а U+0430).
    normalised = unicodedata.normalize("NFKC", content)

    patterns = _COMPILED.get(scope)
    if patterns is None:
        raise ValueError(f"scan_for_threats: unknown scope {scope!r}")
    for compiled, pid in patterns:
        if compiled.search(normalised):
            findings.append(pid)

    return findings


__all__ = [
    "INVISIBLE_CHARS",
    "MAX_SCAN_CHARS",
    "scan_for_threats",
]
