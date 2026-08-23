from __future__ import annotations
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any

EVIDENCE_FILE = 'okf-v0.2-evidence.json'
EXPECTED_SCHEMA_VERSION = 1


def _rfc8785_canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_excerpt(raw: str) -> str:
    s = unicodedata.normalize('NFC', raw)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(line.rstrip() for line in s.split('\n'))


def _compute_artifact_digest(rules: list[dict]) -> str:
    canonical = _rfc8785_canonical(rules)
    return 'sha256:' + _sha256_hex(canonical)


def load_and_verify(scripts_dir: Path) -> tuple[dict | None, str | None]:
    path = scripts_dir / EVIDENCE_FILE
    if not path.exists():
        return None, 'evidence-missing'
    try:
        text = path.read_text('utf-8')
        data = json.loads(text)
    except Exception:
        return None, 'evidence-unreadable'
    if data.get('schema_version') != EXPECTED_SCHEMA_VERSION:
        return None, 'evidence-invalid'
    rules = data.get('rules')
    if not isinstance(rules, list) or not rules:
        return None, 'evidence-invalid'
    for rule in rules:
        raw = rule.get('excerpt_raw', '')
        normalized = _normalize_excerpt(raw)
        expected_sha = rule.get('excerpt_sha256', '')
        actual_sha = _sha256_hex(normalized.encode('utf-8'))
        if actual_sha != expected_sha:
            return None, 'evidence-invalid'
        if normalized != rule.get('excerpt_normalized', ''):
            return None, 'evidence-invalid'
    computed_digest = _compute_artifact_digest(rules)
    if computed_digest != data.get('artifact_digest', ''):
        return None, 'evidence-invalid'
    return data, None


def active_rule_ids(evidence: dict) -> set[str]:
    return {r['rule_id'] for r in evidence.get('rules', [])}
