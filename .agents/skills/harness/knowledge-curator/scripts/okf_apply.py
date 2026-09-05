from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

def _git(repo_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    return subprocess.run(['git', *args], cwd=str(repo_dir), capture_output=True, text=True, env=env_vars)

def _is_clean(repo_dir: Path) -> bool:
    r = _git(repo_dir, 'status', '--porcelain')
    return r.returncode == 0 and not r.stdout.strip()

def _check_conflicts(items: list[dict], bundle_root: Path) -> tuple[bool, str | None]:
    destinations = set()
    sources = set()
    for item in items:
        if not item.get('destination'):
            continue
        dest = item['destination']
        src = item['source']
        if dest in destinations:
            return False, f"Conflict: multiple items moving to {dest}"
        if (bundle_root / dest).exists():
            return False, f"Conflict: destination {dest} already exists in the bundle"
        destinations.add(dest)
        sources.add(src)

    for item in items:
        if not item.get('destination'):
            continue
        dest = item['destination']
        if dest in sources:
            return False, f"Rename chain detected involving {dest}"

    return True, None

def apply_plan(plan_path: str, bundle_path: str, staging_only: bool) -> dict:
    bundle_root = Path(bundle_path).resolve()

    if not _is_clean(bundle_root):
        return {'ok': False, 'code': 1, 'message': 'Target repository has uncommitted changes.'}

    try:
        plan_data = json.loads(Path(plan_path).read_text('utf-8'))
    except Exception as e:
        return {'ok': False, 'code': 1, 'message': f'Failed to read plan: {e}'}

    items = [it for it in plan_data.get('items', []) if it.get('approved')]

    if not items:
        return {'ok': True, 'code': 0, 'message': 'No approved items in plan to apply.'}

    ok, err = _check_conflicts(items, bundle_root)
    if not ok:
        return {'ok': False, 'code': 1, 'message': err}

    with tempfile.TemporaryDirectory() as tmpdir:
        staging_dir = Path(tmpdir) / 'staging'
        subprocess.run(['cp', '-R', str(bundle_root), str(staging_dir)], check=True)

        for item in items:
            src = item.get('source')
            dest = item.get('destination')
            if not src or not dest:
                continue

            src_path = staging_dir / src
            dest_path = staging_dir / dest
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            _git(staging_dir, 'mv', src, dest)

        from okf_inspect import inspect_bundle
        result = inspect_bundle(str(staging_dir), strict=True)

        if result['summary']['errors'] > 0:
            return {
                'ok': False,
                'code': 1,
                'message': 'Staging validation failed after applying moves.',
                'findings': result['findings']
            }

        if staging_only:
            return {'ok': True, 'code': 0, 'message': 'Staging apply successful and validated.', 'staged_items': len(items)}

        journal_dir = Path.home() / '.cache' / 'knowledge-curator' / 'transactions' / plan_data.get('plan_digest', 'unknown')
        journal_dir.mkdir(parents=True, exist_ok=True)
        (journal_dir / 'journal.log').write_text('APPLY_START\n', 'utf-8')

        try:
            for item in items:
                src = item.get('source')
                dest = item.get('destination')
                if not src or not dest:
                    continue
                dest_full = bundle_root / dest
                dest_full.parent.mkdir(parents=True, exist_ok=True)
                _git(bundle_root, 'mv', src, dest)

            (journal_dir / 'journal.log').write_text('APPLY_COMPLETE\n', 'utf-8')
            return {'ok': True, 'code': 0, 'message': 'Project apply successful.', 'applied_items': len(items)}

        except Exception as e:
            _git(bundle_root, 'reset', '--hard', 'HEAD')
            (journal_dir / 'journal.log').write_text(f'APPLY_FAILED: {e}\n', 'utf-8')
            return {'ok': False, 'code': 1, 'message': f'Apply failed, rolled back: {e}'}
