#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--worktree', action='store_true')
parser.add_argument('--staged', action='store_true')
parser.add_argument('--stage-allowlisted', action='store_true')
parser.add_argument('--require-staged-equals-allowlist', action='store_true')
args = parser.parse_args()
manifest = json.loads((ROOT / 'config/public-boundary.json').read_text())
paths = set(manifest['paths']) | {'LICENSE','README.md','README.ko.md','CONTRIBUTING.md','SECURITY.md','.gitignore','.gitattributes','setup.sh','config/public-boundary.json','docs/maintainers/release-checklist.md','scripts/security/check-license.py','scripts/security/scan-public-boundary.py','scripts/security/verify-public-repo.sh','scripts/security/check-identities.py','scripts/security/pre-commit','scripts/security/install-hooks.sh','scripts/verify-public-test-suite.sh','scripts/verify-clean-install.sh','.github/workflows/security.yml','.github/workflows/test.yml'}
bad_markers = ('/' + 'home/', '/' + 'Users/', 'gabrielwith' + 'happy@gmail.com', 'gabriel' + 'yang', 'BEGIN ' + 'PRIVATE KEY', 'gh' + 'p_')
if args.stage_allowlisted:
    subprocess.run(['git','-C',str(ROOT),'add','--',*sorted(paths)], check=True)
def staged():
    return set(subprocess.check_output(['git','-C',str(ROOT),'diff','--cached','--name-only'], text=True).splitlines())
def check_files(files):
    for name in files:
        if name not in paths:
            raise SystemExit(f'FAIL public-boundary forbidden-path={name}')
        target=ROOT/name
        if target.is_file() and any(marker in target.read_text(encoding='utf-8',errors='ignore') for marker in bad_markers):
            raise SystemExit(f'FAIL public-boundary forbidden-content path={name}')
if args.worktree:
    check_files(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '.git/' not in p.as_posix())
if args.staged or args.require_staged_equals_allowlist:
    names=staged(); check_files(names)
    if args.require_staged_equals_allowlist and names != paths:
        raise SystemExit('FAIL public-boundary staged-allowlist-mismatch')
print(f'PASS public-boundary worktree={len(paths)} staged={len(staged())}')
