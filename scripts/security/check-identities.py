#!/usr/bin/env python3
import sys
allowed = 'gabrielwith' + 'happy@gmail.com'
for line in sys.stdin:
    if allowed not in line:
        raise SystemExit('FAIL public-git-identities')
print('PASS public-git-identities')
