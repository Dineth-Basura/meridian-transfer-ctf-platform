#!/usr/bin/env python3
"""Deterministic synthetic Dispatch Window evidence, source MERIDIAN-MT03-V1."""
import base64
import hashlib
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = 'MERIDIAN-MT03-V1'
RELEASE_DATE = date.fromisoformat('2026-10-17')
TOKEN = 'sealed_quay_receipt'
FLAG = f'MT{{mt03_{TOKEN}}}'

def caesar_ascii(text: str, key: int) -> str:
    """Shift only ASCII A-Z and a-z; leave every other character intact."""
    key %= 26
    out = []
    for char in text:
        code = ord(char)
        if 65 <= code <= 90:
            out.append(chr(65 + (code - 65 + key) % 26))
        elif 97 <= code <= 122:
            out.append(chr(97 + (code - 97 + key) % 26))
        else:
            out.append(char)
    return ''.join(out)

def release_notice() -> str:
    return (f'MERIDIAN TRANSFER\nRELEASE NOTICE\nReference: {SOURCE_ID}/RN-04\n\n'
            f'Approved release date:\n{RELEASE_DATE.isoformat()}\n\n'
            'The handover desk approved the fictional research-data parcel for the next dispatch window.\n'
            'The archived training utility indexed its alphabet shift using the calendar day of the approved release.\n'
            'This notice and the transformed dispatch were retained together for review.\n')

def plaintext() -> str:
    return ('MERIDIAN TRANSFER\nDISPATCH RECORD\n\n'
            'Dispatch ID: MT-DW-41\n'
            'Release window: 06:30-07:15 / bay_4\n'
            'Transfer reference: QF-208\n\n'
            'The sealed research-data parcel may leave the fictional quay after desk approval.\n'
            'Keep the receipt with the handover ledger; do not route it to a real address.\n\n'
            f'Verification token: {FLAG}\n')

def build() -> dict[str, str]:
    key = RELEASE_DATE.day % 26
    if not 1 <= key <= 25:
        raise ValueError('Release day produces an invalid shift')
    if not re.fullmatch(r'MT\{mt03_[a-z0-9_]+\}', FLAG):
        raise ValueError('Invalid MT-03 flag format')
    original = plaintext()
    if original.count(FLAG) != 1 or len(re.findall(r'MT\{mt03_[a-z0-9_]+\}', original)) != 1:
        raise ValueError('Plaintext must contain exactly one MT-03 flag')
    shifted = caesar_ascii(original, key)
    encoded = base64.b64encode(shifted.encode('utf-8'))
    recovered = caesar_ascii(base64.b64decode(encoded, validate=True).decode('utf-8'), -key)
    if recovered != original:
        raise AssertionError('Complete transformation round trip failed')
    public, private = ROOT/'public', ROOT/'private'
    public.mkdir(exist_ok=True); private.mkdir(exist_ok=True)
    ciphertext = encoded + b'\n'
    notice = release_notice().encode('utf-8')
    if not notice.endswith(b'\n') or notice.endswith(b'\n\n'):
        raise AssertionError('Notice must end with exactly one LF')
    (public/'dispatch_ciphertext.txt').write_bytes(ciphertext)
    (public/'release_notice.txt').write_bytes(notice)
    (private/'plaintext.txt').write_text(original, encoding='utf-8')
    (private/'flag.txt').write_text(FLAG+'\n', encoding='utf-8')
    (private/'flag.txt').chmod(0o600)
    hashes = {name: hashlib.sha256((public/name).read_bytes()).hexdigest()
              for name in ('dispatch_ciphertext.txt', 'release_notice.txt')}
    (public/'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name,digest in hashes.items()), encoding='ascii')
    print('Built MT-03 public evidence; deterministic source', SOURCE_ID)
    for name,digest in hashes.items():
        print(name, digest)
    return hashes

if __name__ == '__main__':
    build()
