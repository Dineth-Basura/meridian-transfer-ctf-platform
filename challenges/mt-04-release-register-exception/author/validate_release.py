#!/usr/bin/env python3
"""Check source and reviewer materials for accidental literal secret exposure."""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
flag=(ROOT/'private/flag.txt').read_text().strip()
creds=dict(line.split('=',1) for line in (ROOT/'private/credentials.txt').read_text().splitlines())
checks=[]
for name in ('templates','static'):
    files=list((ROOT/'service'/name).rglob('*'))
    checks.append((f'{name} has no flag or training password',all(not p.is_file() or (flag not in p.read_text(errors='ignore') and creds['password'] not in p.read_text(errors='ignore')) for p in files)))
for name in ('Dockerfile','compose.yml','app.py','db.py','seed.py','requirements.txt'):
    text=(ROOT/'service'/name).read_text()
    checks.append((f'{name} contains no literal flag, password or session secret',flag not in text and creds['password'] not in text and not re.search(r'MT04_SESSION_SECRET\s*=\s*[0-9a-f]{24,}',text)))
checks.append(('review package has only expected files', {p.name for p in (ROOT.parents[1]/'review/mt-04-independent').iterdir()}=={'README_REVIEWER.txt','REVIEW_RESULT_TEMPLATE.txt'}))
for name,okay in checks: print(f'[{"PASS" if okay else "FAIL"}] {name}')
ready=all(okay for _,okay in checks); print(f'[{"PASS" if ready else "FAIL"}] release materials ready')
sys.exit(0 if ready else 1)
