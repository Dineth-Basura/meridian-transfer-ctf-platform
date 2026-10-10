#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'digital_footprints.txt', 'README.txt', 'SHA256SUMS'}

def validate(root=ROOT, verbose=True):
    root = Path(root)
    checks = []
    public = root / 'public'
    actual = {p.name for p in public.iterdir()}
    checks.append(('only expected regular public files', actual == EXPECTED and all(not p.is_symlink() and p.is_file() for p in public.iterdir())))
    content = []
    for name in sorted(EXPECTED):
        p = public / name
        try:
            text = p.read_text(encoding='utf-8')
            content.append(text)
            checks.append((name + ' exists and is UTF-8', True))
        except (OSError, UnicodeError):
            checks.append((name + ' exists and is UTF-8', False))
    joined = '\n'.join(content)
    try:
        manifest = (public / 'SHA256SUMS').read_text()
        digest = hashlib.sha256((public / 'digital_footprints.txt').read_bytes()).hexdigest()
        checks.append(('SHA256 manifest', manifest == digest + '  digital_footprints.txt\n'))
        flag = (root / 'private/flag.txt').read_text().strip()
        checks.append(('no final flag', flag not in joined))
        solution = (root / 'private/solution.md').read_text()
        checks.append(('no private solution', solution not in joined and 'Exact flag:' not in joined))
    except OSError:
        checks.append(('author baseline available', False))
    checks.append(('no private filenames or credential markers', not re.search(r'flag\.txt|solution\.md|ctfd_admin_credentials|SECRET_KEY|(?:password|api[_ -]?key|api[_ -]?token|access[_ -]?token|authorization)\s*[:=]|ctfd_[0-9a-f]{32,}', joined, re.I)))
    secrets_dir = ROOT.parents[1] / '.secrets'
    safe = True
    for p in secrets_dir.glob('*'):
        if p.is_file() and (p.suffix in ('.env', '.key', '.pem') or any(word in p.name.lower() for word in ('credential', 'token', 'secret'))):
            try:
                for line in p.read_text().splitlines():
                    if '=' in line and any(k in line.split('=', 1)[0].lower() for k in ('password', 'secret', 'token')):
                        value = line.split('=', 1)[1].strip()
                        if value and value in joined:
                            safe = False
            except UnicodeError:
                safe = False
    key_file = ROOT.parents[1] / 'platform/CTFd/.ctfd_secret_key'
    if key_file.exists():
        key = key_file.read_bytes()
        if key and any(key in text.encode('utf-8') for text in content):
            safe = False
    checks.append(('local secret values absent', safe))
    if verbose:
        for name, ok in checks:
            print(('PASS' if ok else 'FAIL') + ': ' + name)
    return all(ok for _, ok in checks)

if __name__ == '__main__':
    sys.exit(0 if validate() else 1)
