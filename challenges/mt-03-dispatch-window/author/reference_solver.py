#!/usr/bin/env python3
"""Solve MT-03 from public evidence only."""
import base64
import binascii
from datetime import date
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'public'
FLAG_RE = re.compile(r'MT\{mt03_[a-z0-9_]+\}')

def reverse_ascii_shift(text: str, key: int) -> str:
    out = []
    for char in text:
        code = ord(char)
        if 65 <= code <= 90:
            out.append(chr(65 + (code - 65 - key) % 26))
        elif 97 <= code <= 122:
            out.append(chr(97 + (code - 97 - key) % 26))
        else:
            out.append(char)
    return ''.join(out)

def parse_release_key(notice: str) -> tuple[date, int]:
    matches = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', notice)
    if len(matches) != 1:
        raise ValueError('Expected exactly one release date')
    release_date = date.fromisoformat(matches[0])
    key = release_date.day % 26
    if not 1 <= key <= 25:
        raise ValueError('Release date gives an invalid shift')
    return release_date, key

def decode_ciphertext(raw: bytes) -> str:
    if not raw.endswith(b'\n') or raw.endswith(b'\n\n'):
        raise ValueError('Expected one final LF after Base64')
    line = raw[:-1]
    if not line or b'\n' in line or b'\r' in line:
        raise ValueError('Expected one Base64 line')
    try:
        return base64.b64decode(line, validate=True).decode('utf-8')
    except (binascii.Error, UnicodeDecodeError) as error:
        raise ValueError('Invalid Base64 or UTF-8 ciphertext') from error

def solve(public: Path = PUBLIC) -> tuple[str, str, int]:
    notice = (public/'release_notice.txt').read_text(encoding='utf-8')
    _, key = parse_release_key(notice)
    shifted = decode_ciphertext((public/'dispatch_ciphertext.txt').read_bytes())
    original = reverse_ascii_shift(shifted, key)
    flags = FLAG_RE.findall(original)
    if len(flags) != 1:
        raise ValueError(f'Expected exactly one MT-03 flag; found {len(flags)}')
    return original, flags[0], key

if __name__ == '__main__':
    original, flag, key = solve()
    print(f'Derived shift: {key}\nRecovered plaintext:\n{original}\nRecovered flag:\n{flag}')
