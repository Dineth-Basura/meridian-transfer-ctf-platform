#!/usr/bin/env python3
"""Validate only files in public/."""
from pathlib import Path
import hashlib
import re
import sys
from PIL import Image
PUBLIC = Path(__file__).resolve().parents[1]/'public'
def validate():
    names = {'amended_contact_sheet.png', 'SHA256SUMS', 'README.txt'}
    found = {p.name for p in PUBLIC.iterdir()}
    checks = [('expected public files present', found == names)]
    try:
        with Image.open(PUBLIC/'amended_contact_sheet.png') as im:
            im.load(); mode=im.mode; metadata='\n'.join(str(v) for v in im.info.values())
        checks += [('PNG decodes successfully', True), ('PNG mode is RGB', mode == 'RGB'),
                   ('metadata clue present', 'lowest-order red image data' in metadata),
                   ('metadata does not reveal flag', not re.search(r'MT\{mt02_[a-z0-9_]+\}', metadata))]
    except Exception:
        checks += [(name, False) for name in ('PNG decodes successfully','PNG mode is RGB','metadata clue present','metadata does not reveal flag')]
    try:
        expected, filename = (PUBLIC/'SHA256SUMS').read_text().strip().split()
        checksum = filename == 'amended_contact_sheet.png' and hashlib.sha256((PUBLIC/filename).read_bytes()).hexdigest() == expected
    except Exception: checksum=False
    checks.append(('checksum manifest valid', checksum))
    try:
        readme=(PUBLIC/'README.txt').read_text(encoding='utf-8'); valid=True
    except Exception: readme=''; valid=False
    checks += [('UTF-8 README valid', valid), ('no private files present', not (found & {'flag.txt','payload.txt','solution.md','challenge_config.md'}))]
    plain=readme+'\n'+(PUBLIC/'SHA256SUMS').read_text(errors='replace')+'\n'+metadata if 'metadata' in locals() else readme
    checks += [('no administrator credentials present', not re.search(r'ctfd_admin_credentials|administrator\s*password\s*[:=]', plain, re.I)),
               ('no CTFd secret present', not re.search(r'SECRET_KEY\s*=', plain, re.I)),
               ('no obvious API token present', not re.search(r'(?:api[_ -]?token|access[_ -]?token)\s*[:=]', plain, re.I))]
    for name, okay in checks: print(f'[ {"PASS" if okay else "FAIL"} ] {name}'.replace('[ ', '[').replace(' ]', ']'))
    ready=all(okay for _,okay in checks)
    print(f'[{"PASS" if ready else "FAIL"}] public release ready')
    return ready
if __name__ == '__main__': sys.exit(0 if validate() else 1)
