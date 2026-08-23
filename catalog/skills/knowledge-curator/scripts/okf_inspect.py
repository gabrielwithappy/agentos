from __future__ import annotations
import hashlib
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

TOOL_VERSION = 'knowledge-curator/0.1'
SCHEMA_VERSION = 1
RESERVED_NAMES = frozenset({'index.md', 'log.md'})
TEMPLATE_EXEMPT = frozenset({'_template.md'})
MAX_FILE_BYTES = 1 * 1024 * 1024


def _sha256_file(content: bytes) -> str:
    return 'sha256:' + hashlib.sha256(content).hexdigest()


def _read_safe(path: Path) -> tuple[bytes | None, str | None]:
    if path.is_symlink():
        return None, 'symlink'
    try:
        size = path.stat().st_size
    except OSError:
        return None, 'unreadable'
    if size > MAX_FILE_BYTES:
        return None, 'oversize'
    try:
        data = path.read_bytes()
    except OSError:
        return None, 'unreadable'
    if b'\x00' in data:
        return None, 'binary'
    return data, None


def _parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != '---':
        return None, 'missing'
    closing = None
    for i, line in enumerate(lines[1:], 1):
        if line.rstrip() == '---':
            closing = i
            break
    if closing is None:
        return None, 'unclosed'
    fm_lines = lines[1:closing]
    return _parse_flat_yaml(fm_lines)


def _parse_flat_yaml(lines: list[str]) -> tuple[dict | None, str | None]:
    result: dict[str, Any] = {}
    seen: set[str] = set()
    i = 0
    while i < len(lines):
        raw = lines[i]
        if '\t' in raw:
            return None, 'unsupported'
        stripped = raw.rstrip()
        if not stripped:
            i += 1
            continue
        if stripped.lstrip().startswith(('&', '*', '!', '|', '>')):
            return None, 'unsupported'
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)', stripped)
        if not m:
            return None, 'unsupported'
        key, val_raw = m.group(1), m.group(2).strip()
        if key in seen:
            return None, 'duplicate-key'
        seen.add(key)
        if val_raw == '':
            items: list[str] = []
            i += 1
            while i < len(lines):
                item_line = lines[i]
                if '\t' in item_line:
                    return None, 'unsupported'
                item_stripped = item_line.rstrip()
                if not item_stripped:
                    i += 1
                    continue
                item_m = re.match(r'^(\s*)-[ \t]+(.*)', item_stripped)
                if not item_m:
                    break
                item_val = item_m.group(2).strip()
                if item_val.startswith(('{', '[')):
                    return None, 'unsupported'
                items.append(_unquote_scalar(item_val))
                i += 1
            result[key] = items
        else:
            if val_raw.startswith(('{', '[')):
                return None, 'unsupported'
            result[key] = _unquote_scalar(val_raw)
            i += 1
    return result, None


def _unquote_scalar(s: str) -> str:
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s


def _strip_fenced_and_inline_code(text: str) -> str:
    fenced_re = re.compile(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1', re.MULTILINE | re.DOTALL)
    text = fenced_re.sub(lambda m: '\n' * m.group().count('\n'), text)
    inline_re = re.compile(r'`[^`\n]+`')
    return inline_re.sub(lambda m: ' ' * len(m.group()), text)


def _extract_links(text: str, file_path: Path, root: Path) -> list[dict]:
    clean = _strip_fenced_and_inline_code(text)
    links = []

    html_re = re.compile(r'<a\s[^>]*href\s*=', re.IGNORECASE)
    for m in html_re.finditer(clean):
        links.append({'kind': 'html', 'destination': None, 'finding': 'unsupported-link', 'start': m.start(), 'end': m.end()})

    autolink_re = re.compile(r'<(https?://[^>\s]+)>')
    for m in autolink_re.finditer(clean):
        url = m.group(1)
        parsed = urlparse(url)
        links.append({'kind': 'autolink', 'destination': url, 'external': bool(parsed.scheme), 'start': m.start(), 'end': m.end()})

    ref_def_re = re.compile(r'^\[([^\]]+)\]:\s*(\S+)', re.MULTILINE)
    ref_defs = {}
    for m in ref_def_re.finditer(clean):
        ref_id = m.group(1).strip().lower()
        dest = m.group(2).strip()
        ref_defs[ref_id] = dest
        links.append({'kind': 'reference-definition', 'ref_id': ref_id, 'destination': dest, 'start': m.start(), 'end': m.end(), **_classify_dest(dest, file_path, root)})

    inline_re = re.compile(r'!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(([^)]+)\)')
    for m in inline_re.finditer(clean):
        raw_dest = m.group(1).strip()
        is_image = clean[m.start()] == '!'
        kind = 'image' if is_image else 'inline'
        links.append({'kind': kind, 'destination': raw_dest, 'start': m.start(), 'end': m.end(), **_classify_dest(raw_dest, file_path, root)})

    ref_use_re = re.compile(r'(?<!!)\[([^\]]+)\]\[([^\]]*)\]')
    for m in ref_use_re.finditer(clean):
        ref_id = (m.group(2).strip() or m.group(1).strip()).lower()
        dest = ref_defs.get(ref_id)
        links.append({'kind': 'reference-use', 'ref_id': ref_id, 'destination': dest, 'start': m.start(), 'end': m.end(), **(   _classify_dest(dest, file_path, root) if dest else {'external': False, 'internal': False, 'unresolved': True})})

    return links


def _classify_dest(dest: str, file_path: Path, root: Path) -> dict:
    if dest is None:
        return {'external': False, 'internal': False, 'unresolved': True}
    parsed = urlparse(dest)
    if parsed.scheme or parsed.netloc:
        return {'external': True, 'internal': False}
    if dest.startswith('#'):
        return {'external': False, 'internal': False, 'fragment_only': True}
    path_part = unquote(parsed.path)
    if not path_part:
        return {'external': False, 'internal': False, 'fragment_only': True}
    try:
        resolved = (file_path.parent / path_part).resolve()
        resolved.relative_to(root.resolve())
        bundle_rel = str(resolved.relative_to(root.resolve()))
        return {'external': False, 'internal': True, 'bundle_path': bundle_rel}
    except (ValueError, OSError):
        return {'external': False, 'internal': False, 'path_traversal': True}


def _is_meaningful_dir(dirpath: Path, root: Path) -> bool:
    if dirpath == root:
        return True
    for item in dirpath.iterdir():
        if item.is_dir() and not item.is_symlink():
            return True
        if item.is_file() and item.suffix == '.md' and item.name not in RESERVED_NAMES:
            return True
    return False


def _collect_files(root: Path) -> list[dict]:
    records = []
    for dirpath_str, dirnames, filenames in os.walk(str(root)):
        current = Path(dirpath_str)
        if current.is_symlink():
            dirnames[:] = []
            continue
        if '.git' in dirnames:
            dirnames.remove('.git')
        dirnames[:] = [d for d in sorted(dirnames) if not Path(dirpath_str, d).is_symlink()]
        
        for fname in sorted(filenames):
            if not fname.endswith('.md'):
                continue
            fpath = current / fname
            rel = str(fpath.relative_to(root))
            data, err = _read_safe(fpath)
            if err:
                records.append({'path': rel, 'error': err, 'reserved': fname in RESERVED_NAMES})
                continue
            digest = _sha256_file(data)
            text = data.decode('utf-8')
            is_reserved = fname in RESERVED_NAMES
            is_template_exempt = fname in TEMPLATE_EXEMPT
            fm, fm_err = _parse_frontmatter(text)
            rec = {
                'path': rel,
                'digest': digest,
                'reserved': is_reserved,
                'template_exempt': is_template_exempt,
                'frontmatter_error': fm_err,
            }
            if fm and not fm_err:
                rec['type'] = fm.get('type')
                rec['title'] = fm.get('title')
                rec['description'] = fm.get('description')
                rec['tags'] = fm.get('tags')
                rec['status'] = fm.get('status')
            links = _extract_links(text, fpath, root)
            rec['links'] = links
            records.append(rec)
    return records


def _compute_findings(files: list[dict], root: Path, strict: bool, active_rules: set[str]) -> list[dict]:
    findings = []

    root_has_log = any(f['path'] == 'log.md' for f in files)

    if not root_has_log:
        sev = 'error' if strict else 'warning'
        findings.append(_finding('missing-root-log', 'log.md', sev, 'project', 'Root log.md is missing'))

    for f in files:
        if f.get('error'):
            continue
        for link in f.get('links', []):
            if link.get('finding') == 'unsupported-link':
                findings.append(_finding('unsupported-link', f['path'], 'error', 'project', 'HTML link found; apply is blocked'))

    for f in files:
        if f.get('error'):
            findings.append(_finding(f['error'], f['path'], 'error', 'project', f"File cannot be read: {f['error']}"))
            continue
        path = f['path']
        is_reserved = f.get('reserved', False)

        if is_reserved:
            continue

        if 'okf-type-required' in active_rules:
            if f.get('frontmatter_error') in ('missing', 'unclosed', 'unsupported', 'duplicate-key'):
                findings.append(_finding('okf-frontmatter-invalid', path, 'error', 'okf-v0.2', f"Frontmatter error: {f.get('frontmatter_error')}"))
            elif f.get('frontmatter_error') is None:
                t = f.get('type')
                if not t or (isinstance(t, str) and not t.strip()):
                    findings.append(_finding('okf-type-missing', path, 'error', 'okf-v0.2', 'Non-empty type field is required'))

    for dirpath_str, dirnames, filenames in os.walk(str(root)):
        current = Path(dirpath_str)
        if current.is_symlink():
            continue
        if '.git' in dirnames:
            dirnames.remove('.git')
        dirnames[:] = [d for d in sorted(dirnames) if not Path(dirpath_str, d).is_symlink()]
        if not _is_meaningful_dir(current, root):
            continue
        has_index = (current / 'index.md').exists()
        if not has_index:
            sev = 'error' if strict else 'warning'
            index_path = str((current / 'index.md').relative_to(root))
            findings.append(_finding('missing-index', index_path, sev, 'project', 'Meaningful directory has no index.md'))

    return findings


def _finding(rule_id: str, path: str, severity: str, source: str, message: str) -> dict:
    return {'rule_id': rule_id, 'path': path, 'severity': severity, 'source': source, 'message': message}


def inspect_bundle(
    bundle_path: str,
    strict: bool = False,
    evidence: dict | None = None,
    evidence_digest: str | None = None,
    evidence_gate_commit: str | None = None,
) -> dict:
    root = Path(bundle_path).resolve()

    if not root.exists() or root.is_symlink():
        return {
            'schema_version': SCHEMA_VERSION,
            'tool_version': TOOL_VERSION,
            'evidence_gate_commit': evidence_gate_commit,
            'evidence_artifact_digest': evidence_digest,
            'bundle_root': str(root),
            'files': [],
            'findings': [_finding('bundle-root-missing', str(root), 'error', 'project', 'Bundle root does not exist or is a symlink')],
            'summary': {'total_files': 0, 'errors': 1, 'warnings': 0},
        }

    active_rules: set[str] = set()
    if evidence:
        active_rules = {r['rule_id'] for r in evidence.get('rules', [])}

    files = _collect_files(root)
    findings = _compute_findings(files, root, strict, active_rules)

    errors = sum(1 for f in findings if f['severity'] == 'error')
    warnings = sum(1 for f in findings if f['severity'] == 'warning')

    return {
        'schema_version': SCHEMA_VERSION,
        'tool_version': TOOL_VERSION,
        'evidence_gate_commit': evidence_gate_commit,
        'evidence_artifact_digest': evidence_digest,
        'bundle_root': str(root),
        'files': files,
        'findings': findings,
        'summary': {'total_files': len(files), 'errors': errors, 'warnings': warnings},
    }
