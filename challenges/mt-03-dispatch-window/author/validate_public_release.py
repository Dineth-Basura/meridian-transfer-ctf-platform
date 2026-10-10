#!/usr/bin/env python3
"""Validate MT-03 release using only public/ files."""
import base64
import binascii
import hashlib
from pathlib import Path
import re
import sys

PUBLIC = Path(__file__).resolve().parents[1]/'public'
EXPECTED = {'dispatch_ciphertext.txt', 'release_notice.txt', 'SHA256SUMS', 'README.txt'}
FLAG_RE = re.compile(r'MT\{mt03_[a-z0-9_]+\}')

def validate() -> bool:
    found = {p.name for p in PUBLIC.iterdir()}
    checks = [('expected files present', found == EXPECTED)]
    raw = (PUBLIC/'dispatch_ciphertext.txt').read_bytes() if 'dispatch_ciphertext.txt' in found else b''
    ascii_safe = raw.isascii() and raw.endswith(b'\n') and not raw.endswith(b'\n\n') and b'\n' not in raw[:-1]
    checks.append(('ciphertext ASCII-safe', ascii_safe))
    try:
        decoded = base64.b64decode(raw[:-1], validate=True) if ascii_safe else None
        valid_base64 = decoded is not None and bool(decoded)
    except binascii.Error:
        valid_base64 = False
    checks.append(('ciphertext valid Base64', valid_base64))
    try:
        notice = (PUBLIC/'release_notice.txt').read_text(encoding='utf-8')
        utf8 = True
    except (OSError, UnicodeDecodeError):
        notice = ''; utf8 = False
    checks.append(('release notice UTF-8', utf8))
    checks.append(('exactly one release date', len(re.findall(r'\b\d{4}-\d{2}-\d{2}\b', notice)) == 1))
    try:
        rows = (PUBLIC/'SHA256SUMS').read_text(encoding='ascii').splitlines()
        parsed = [re.fullmatch(r'([0-9a-f]{64})  (dispatch_ciphertext\.txt|release_notice\.txt)', row) for row in rows]
        checksum = len(parsed)==2 and all(parsed) and {m.group(2) for m in parsed} == {'dispatch_ciphertext.txt','release_notice.txt'} and all(hashlib.sha256((PUBLIC/m.group(2)).read_bytes()).hexdigest()==m.group(1) for m in parsed)
    except (OSError, UnicodeDecodeError): checksum = False
    checks.append(('SHA256SUMS valid', checksum))
    try:
        readme = (PUBLIC/'README.txt').read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError): readme = ''
    checks.append(('exact private flag absent from release notice', not FLAG_RE.search(notice)))
    checks.append(('exact private flag absent from README', bool(readme) and not FLAG_RE.search(readme)))
    checks.append(('no private files', not found.intersection({'flag.txt','plaintext.txt','solution.md','challenge_config.md'})))
    plain = notice + '\n' + readme + '\n' + ((PUBLIC/'SHA256SUMS').read_text(errors='replace') if 'SHA256SUMS' in found else '')
    checks.append(('no obvious credentials', not re.search(r'(?i)(?:admin(?:istrator)?[_ -]?password|password)\s*[:=]', plain)))
    checks.append(('no CTFd SECRET_KEY', not re.search(r'(?i)SECRET_KEY\s*[:=]', plain)))
    checks.append(('no obvious API token', not re.search(r'(?i)(?:api[_ -]?token|access[_ -]?token|api[_ -]?key)\s*[:=]', plain)))
    for name,okay in checks:
        print(f'[{"PASS" if okay else "FAIL"}] {name}')
    ready = all(okay for _,okay in checks)
    print(f'[{"PASS" if ready else "FAIL"}] public release ready')
    return ready

if __name__ == '__main__':
    sys.exit(0 if validate() else 1)
