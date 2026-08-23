from __future__ import annotations
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any

TOOL_VERSION = 'knowledge-curator/0.1'
POLICY_VERSION = 'okf-project-policy/1'
SCHEMA_VERSION = 1
RESERVED_NAMES = frozenset({'index.md', 'log.md'})
TEMPLATE_EXEMPT = frozenset({'_template.md'})
AUTO_EXCLUDE = RESERVED_NAMES | TEMPLATE_EXEMPT


def _rfc8785(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _sha256(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def _nfc(s: str) -> str:
    return unicodedata.normalize('NFC', s)


def _tokenize(s: str) -> set[str]:
    import re
    return set(re.findall(r'[^\W_]+', _nfc(s.lower()), flags=re.UNICODE))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _doc_tokens(rec: dict) -> dict[str, set[str]]:
    title = rec.get('title') or ''
    tags = rec.get('tags') or []
    path = rec.get('path') or ''
    links = rec.get('links') or []
    link_text = ' '.join(
        _nfc(lnk.get('bundle_path', '') or '')
        for lnk in links
        if lnk.get('internal') and lnk.get('bundle_path')
    )
    tag_text = ' '.join(tags) if isinstance(tags, list) else ''
    return {
        'title': _tokenize(title),
        'tags': _tokenize(tag_text),
        'path': _tokenize(Path(path).stem),
        'links': _tokenize(link_text),
    }


def _folder_tokens(folder_path: str, folder_files: list[dict]) -> dict[str, set[str]]:
    all_titles = ' '.join((f.get('title') or '') for f in folder_files)
    all_tags: list[str] = []
    for f in folder_files:
        t = f.get('tags') or []
        if isinstance(t, list):
            all_tags.extend(t)
    all_links = ' '.join(
        lnk.get('bundle_path', '') or ''
        for f in folder_files
        for lnk in (f.get('links') or [])
        if lnk.get('internal')
    )
    return {
        'title': _tokenize(all_titles + ' ' + folder_path),
        'tags': _tokenize(' '.join(all_tags)),
        'links': _tokenize(all_links),
    }


def _score_candidate(doc_tokens: dict[str, set[str]], folder_path: str, folder_tokens: dict[str, set[str]]) -> float:
    title_score = _jaccard(doc_tokens.get('title', set()), folder_tokens.get('title', set()))
    tags_score = _jaccard(doc_tokens.get('tags', set()), folder_tokens.get('tags', set()))
    link_score = _jaccard(doc_tokens.get('links', set()), folder_tokens.get('links', set()))
    folder_score = _jaccard(doc_tokens.get('path', set()), _tokenize(folder_path))
    return round(title_score * 0.35 + tags_score * 0.30 + link_score * 0.25 + folder_score * 0.10, 4)


def _compute_inventory_digest(files: list[dict]) -> str:
    records = sorted(
        [
            {
                'digest': f.get('digest'),
                'path': f['path'],
                'reserved': f.get('reserved', False),
                'tags': f.get('tags'),
                'title': f.get('title'),
                'type': f.get('type'),
            }
            for f in files
        ],
        key=lambda x: x['path'],
    )
    return _sha256(_rfc8785(records))


def _compute_target_identity(bundle_root: Path) -> dict:
    import subprocess
    git_dir = bundle_root
    while git_dir != git_dir.parent:
        if (git_dir / '.git').exists():
            break
        git_dir = git_dir.parent

    def _git(*args: str) -> str | None:
        r = subprocess.run(['git', *args], cwd=str(git_dir), capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else None

    head = _git('rev-parse', 'HEAD')
    common_dir = _git('rev-parse', '--git-common-dir')
    repo_id_parts = {'head': head, 'path': str(bundle_root)}
    repo_identity = _sha256(_rfc8785(repo_id_parts))
    return {
        'target_git_common_dir_identity': _sha256(str(common_dir).encode('utf-8')) if common_dir else None,
        'target_head': f'git:{head}' if head else None,
        'target_repo_identity': repo_identity,
    }


def _build_folder_index(files: list[dict]) -> dict[str, list[dict]]:
    folders: dict[str, list[dict]] = {}
    for f in files:
        folder = str(Path(f['path']).parent)
        folders.setdefault(folder, []).append(f)
    return folders


def _find_best_destination(
    doc: dict,
    doc_tokens: dict[str, set[str]],
    folders: dict[str, list[dict]],
    current_folder: str,
) -> tuple[str | None, float]:
    best_path = None
    best_score = 0.0
    doc_name = Path(doc['path']).name
    for folder_path, folder_files in sorted(folders.items()):
        if folder_path == current_folder:
            continue
        if any(Path(f['path']).name == doc_name for f in folder_files):
            continue
        ft = _folder_tokens(folder_path, [f for f in folder_files if not f.get('reserved')])
        score = _score_candidate(doc_tokens, folder_path, ft)
        if score > best_score or (score == best_score and (best_path is None or folder_path < best_path)):
            best_score = score
            best_path = folder_path
    if best_score < 0.80:
        return None, best_score
    return best_path, best_score


def _item_digest(item: dict) -> str:
    projection = {
        'confidence': item['confidence'],
        'destination': item['destination'],
        'evidence': item['evidence'],
        'id': item['id'],
        'policy_version': POLICY_VERSION,
        'reason': item['reason'],
        'schema_version': SCHEMA_VERSION,
        'source': item['source'],
        'source_digest': item['source_digest'],
    }
    return _sha256(_rfc8785(projection))


def _affected_record(op_id: str, pre_path: str | None, post_path: str | None, pre_digest: str | None) -> dict:
    if pre_path and post_path:
        return {'image_kind': 'both', 'operation_id': op_id, 'post_digest': None, 'post_path': post_path, 'pre_digest': pre_digest, 'pre_path': pre_path}
    if pre_path:
        return {'image_kind': 'pre', 'operation_id': op_id, 'post_digest': None, 'post_path': None, 'pre_digest': pre_digest, 'pre_path': pre_path}
    return {'image_kind': 'post', 'operation_id': op_id, 'post_digest': None, 'post_path': post_path, 'pre_digest': None, 'pre_path': None}


def _graph_digest(items: list[dict]) -> str:
    edges = sorted(
        [{'destination': it['destination'], 'id': it['id'], 'source': it['source']} for it in items],
        key=lambda x: x['id'],
    )
    return _sha256(_rfc8785({'cycle_free': True, 'edges': edges}))


def _plan_digest(plan: dict) -> str:
    projection = {k: v for k, v in plan.items() if k != 'plan_digest'}
    projection['plan_digest'] = 'sha256:pending'
    return _sha256(_rfc8785(projection))


def generate_plan(
    bundle_path: str,
    files: list[dict],
    evidence: dict,
    evidence_digest: str,
    evidence_gate_commit: str | None,
) -> dict:
    root = Path(bundle_path).resolve()
    inventory_digest = _compute_inventory_digest(files)
    target_identity = _compute_target_identity(root)
    folders = _build_folder_index(files)

    concept_files = [
        f for f in files
        if not f.get('error')
        and not f.get('reserved')
        and not f.get('template_exempt')
        and Path(f['path']).name not in AUTO_EXCLUDE
        and f.get('frontmatter_error') is None
    ]

    items = []
    affected_files = []

    for idx, doc in enumerate(sorted(concept_files, key=lambda x: x['path']), 1):
        op_id = f'move-{idx:03d}'
        current_folder = str(Path(doc['path']).parent)
        doc_tok = _doc_tokens(doc)
        dest_folder, score = _find_best_destination(doc, doc_tok, folders, current_folder)

        if dest_folder is not None:
            dest_path = str(Path(dest_folder) / Path(doc['path']).name)
            evidence_refs = [doc['path'], f'score:{score:.4f}']
        else:
            dest_path = None
            evidence_refs = [doc['path'], f'score:{score:.4f}', 'below-threshold']

        item = {
            'approved': False,
            'approved_at': None,
            'approved_by': None,
            'approved_item_digest': None,
            'approval_key_id': None,
            'approval_signature': None,
            'approval_signature_algorithm': None,
            'approval_signed_payload_digest': None,
            'confidence': 'review',
            'destination': dest_path,
            'evidence': evidence_refs,
            'id': op_id,
            'index_updates': [],
            'item_digest': 'sha256:pending',
            'manual_required': False,
            'reason': f'Jaccard-weighted score {score:.4f} against existing folder groups',
            'source': doc['path'],
            'source_digest': doc.get('digest'),
        }
        item['item_digest'] = _item_digest(item)
        items.append(item)

        if dest_path:
            affected_files.append(_affected_record(op_id, doc['path'], dest_path, doc.get('digest')))
        else:
            affected_files.append(_affected_record(op_id, doc['path'], None, doc.get('digest')))

    candidate_graph_digest = _graph_digest(items)
    candidate_affected_files_digest = _sha256(_rfc8785(sorted(
        affected_files, key=lambda x: (x['pre_path'] or '', x['post_path'] or '')
    )))

    parser_policy = {
        'extensions': ['autolink', 'strikethrough', 'table', 'tagfilter', 'tasklist'],
        'implementation': 'stdlib-regex-subset',
        'name': 'cmark-gfm',
        'percent_decoding': 'path-only',
        'slug_algorithm': 'github-gfm',
        'unicode_normalization': 'NFC',
        'version': '0.29.0.gfm.13',
    }

    plan: dict = {
        'affected_files': affected_files,
        'approval_set_digest': _sha256(b'{}'),
        'base_plan_digest': 'sha256:pending',
        'baseline_findings': [],
        'baseline_mappings': [],
        'bundle_root': str(root),
        'candidate_affected_files_digest': candidate_affected_files_digest,
        'candidate_graph_digest': candidate_graph_digest,
        'created_directories': [],
        'created_files': [],
        'created_from': inventory_digest,
        'effective_affected_files': [],
        'effective_affected_files_digest': _sha256(_rfc8785([])),
        'effective_graph_digest': _graph_digest([]),
        'effective_items': [],
        'evidence_artifact_digest': evidence_digest,
        'evidence_gate_commit': evidence_gate_commit,
        'external_scope_ack': None,
        'inventory_digest': inventory_digest,
        'items': items,
        'options': {'strict': False},
        'parser_policy': parser_policy,
        'plan_digest': 'sha256:pending',
        'policy_version': POLICY_VERSION,
        'project_root': str(root),
        'schema_version': SCHEMA_VERSION,
        'tool_version': TOOL_VERSION,
        **target_identity,
    }

    base_projection = {
        k: v for k, v in plan.items()
        if k not in ('approval_set_digest', 'base_plan_digest', 'effective_affected_files', 'effective_affected_files_digest', 'effective_graph_digest', 'effective_items', 'plan_digest')
    }
    plan['base_plan_digest'] = _sha256(_rfc8785(base_projection))
    plan['plan_digest'] = _plan_digest(plan)

    return plan
