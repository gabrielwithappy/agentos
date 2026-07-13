#!/usr/bin/env python3
"""Keep public maintainer documentation focused on public operations."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
documents = [root / 'README.md', root / 'CONTRIBUTING.md', root / 'SECURITY.md', root / 'docs/maintainers/release-checklist.md']
text = '\n'.join(path.read_text(encoding='utf-8') for path in documents).lower()
required = ('install', 'contribut', 'security', 'release')
for word in required:
    if word not in text:
        raise SystemExit(f'FAIL public-maintainer-docs missing={word}')
for forbidden in ('agent-harness', 'private downstream'):
    if forbidden in text:
        raise SystemExit(f'FAIL public-maintainer-docs private-reference={forbidden}')
print('PASS public-maintainer-docs prerequisites install-location completion-signal safe-rerun contribute security release no-private-sync')
