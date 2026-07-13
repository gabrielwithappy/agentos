#!/usr/bin/env python3
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--license', required=True)
parser.add_argument('--spdx', required=True)
parser.add_argument('--require-canonical-text', action='store_true')
parser.add_argument('--copyright', required=True)
args = parser.parse_args()
text = Path(args.license).read_text(encoding='utf-8')
if args.spdx != 'MIT' or not text.startswith('MIT License\n') or args.copyright not in text:
    raise SystemExit('FAIL canonical-license')
print(f'PASS canonical-license SPDX={args.spdx} copyright={args.copyright}')
