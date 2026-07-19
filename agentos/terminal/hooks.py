from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentos.llm.redaction import redact_text
from agentos.terminal.paths import StateError, agentos_home, atomic_write_text, ensure_contained

HOOK_SCHEMA_VERSION = "agentos.hooks/v1"
MAX_CONTEXT_BYTES = 65536


class HookError(ValueError):
    def __init__(self, message: str, *, critical: bool = True, hook: str = "input"):
        self.critical = critical
        self.hook = hook
        super().__init__(message)


@dataclass(frozen=True)
class HookSpec:
    name: str
    phase: str
    enabled: bool
    order: int
    critical: bool
    timeout_ms: int
    value: Any = None


DEFAULTS: dict[str, HookSpec] = {
    "trim_whitespace": HookSpec("trim_whitespace", "input", True, 10, True, 2000),
    "reject_empty": HookSpec("reject_empty", "input", True, 20, True, 2000),
    "max_input_chars": HookSpec("max_input_chars", "input", True, 30, True, 2000, 20000),
    "prepend_context_file": HookSpec("prepend_context_file", "input", False, 40, True, 2000, ""),
    "record_turn_metrics": HookSpec("record_turn_metrics", "metrics", True, 900, False, 2000),
}

ALLOWED_FIELDS = {"enabled", "order", "critical", "timeout_ms", "value"}


def _config_path(home: str | Path | None = None) -> Path:
    return agentos_home(home) / "config.toml"


def _load_raw(home: str | Path | None = None) -> dict[str, Any]:
    path = _config_path(home)
    if not path.exists():
        return {"schema_version": HOOK_SCHEMA_VERSION, "hooks": {}}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def effective_hooks(home: str | Path | None = None) -> list[HookSpec]:
    raw = _load_raw(home)
    if raw.get("schema_version", HOOK_SCHEMA_VERSION) != HOOK_SCHEMA_VERSION:
        raise StateError("Unsupported hook config schema.")
    hooks = raw.get("hooks", {})
    if not isinstance(hooks, dict):
        raise StateError("Hook config [hooks] must be a table.")
    specs = []
    for name, default in DEFAULTS.items():
        entry = hooks.get(name, {})
        if entry is None:
            entry = {}
        if not isinstance(entry, dict):
            raise StateError(f"Hook {name} config must be a table.")
        unknown = set(entry) - ALLOWED_FIELDS
        if unknown:
            raise StateError(f"Unknown fields for hook {name}: {', '.join(sorted(unknown))}")
        order = int(entry.get("order", default.order))
        timeout_ms = int(entry.get("timeout_ms", default.timeout_ms))
        if not 0 <= order <= 999:
            raise StateError(f"Hook {name} order must be 0..999.")
        if not 1 <= timeout_ms <= 2000:
            raise StateError(f"Hook {name} timeout_ms must be 1..2000.")
        specs.append(
            HookSpec(
                name=name,
                phase=default.phase,
                enabled=bool(entry.get("enabled", default.enabled)),
                order=order,
                critical=bool(entry.get("critical", default.critical)),
                timeout_ms=timeout_ms,
                value=entry.get("value", default.value),
            )
        )
    return sorted(specs, key=lambda item: (item.phase, item.order, item.name))


def set_hook_enabled(name: str, enabled: bool, home: str | Path | None = None) -> None:
    if name not in DEFAULTS:
        raise StateError(f"Unknown hook {name}.")
    current = {spec.name: spec for spec in effective_hooks(home)}
    current[name] = HookSpec(
        name=name,
        phase=current[name].phase,
        enabled=enabled,
        order=current[name].order,
        critical=current[name].critical,
        timeout_ms=current[name].timeout_ms,
        value=current[name].value,
    )
    lines = [f'schema_version = "{HOOK_SCHEMA_VERSION}"', "", "[hooks]"]
    for spec in sorted(current.values(), key=lambda item: item.name):
        lines.append("")
        lines.append(f"[hooks.{spec.name}]")
        lines.append(f"enabled = {str(spec.enabled).lower()}")
        lines.append(f"order = {spec.order}")
        lines.append(f"critical = {str(spec.critical).lower()}")
        lines.append(f"timeout_ms = {spec.timeout_ms}")
        if spec.value not in (None, ""):
            lines.append(f'value = "{redact_text(str(spec.value))}"')
    atomic_write_text(_config_path(home), "\n".join(lines) + "\n")


def apply_input_hooks(prompt: str, home: str | Path | None = None) -> str:
    result = prompt
    root = agentos_home(home)
    for spec in effective_hooks(root):
        if not spec.enabled or spec.phase != "input":
            continue
        try:
            if spec.name == "trim_whitespace":
                result = result.strip()
            elif spec.name == "reject_empty" and not result.strip():
                raise HookError("Input is empty. Next: enter a prompt with visible text.", hook=spec.name)
            elif spec.name == "max_input_chars" and len(result) > int(spec.value):
                raise HookError(f"Input exceeds max_input_chars={spec.value}.", hook=spec.name)
            elif spec.name == "prepend_context_file" and spec.value:
                basename = Path(str(spec.value)).name
                if basename != str(spec.value) or not basename.endswith(".md"):
                    raise HookError("Context file must be a direct .md basename.", hook=spec.name)
                path = ensure_contained(root / "context" / basename, root / "context")
                if path.is_symlink() or not path.is_file():
                    raise HookError("Context file must be a regular file.", hook=spec.name)
                if path.stat().st_size > MAX_CONTEXT_BYTES:
                    raise HookError("Context file is larger than 65536 bytes.", hook=spec.name)
                result = path.read_text(encoding="utf-8") + "\n\n" + result
        except HookError:
            raise
        except Exception as exc:
            if spec.critical:
                raise HookError("Hook failed. Next: agentos hook config show", hook=spec.name) from exc
    return result
