#!/usr/bin/env python3
"""Inspect public release only; derive comparison values from public evidence."""
import argparse
import csv
import io
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from reference_solver import ROOT, FILES, HEADERS, unpack, solve

def validate(public,verbose=True):
    def check(label,condition):
        if not condition: raise ValueError(label)
        if verbose: print('[PASS] '+label)
    check('expected public files',{p.name for p in public.iterdir()}=={'mt05_evidence.zip','SHA256SUMS','README.txt'})
    archive=public/'mt05_evidence.zip'
    check('archive below 50 MiB',archive.stat().st_size<50*1024**2)
    with zipfile.ZipFile(archive) as z:
        check('ZIP valid',z.testzip() is None)
        names=z.namelist()
        check('no path traversal entries in ZIP',all('..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
        check('no absolute archive paths',all(not PurePosixPath(n).is_absolute() and ':' not in n for n in names))
        check('expected inner files',len(names)==6 and set(names)=={'meridian_mt05/'+n for n in (*FILES,'EVIDENCE_SHA256SUMS')})
        check('no private files',all('private' not in n and not n.endswith(('.py','.md')) for n in names))
        blobs=[z.read(n) for n in names]
    with tempfile.TemporaryDirectory() as tmp:
        folder=unpack(public,Path(tmp))
        check('outer SHA256 valid',True); check('inner evidence SHA256 valid',True)
        with (folder/'application_audit.csv').open(newline='') as f:
            r=csv.DictReader(f); check('CSV parseable',r.fieldnames==HEADERS and bool(list(r)))
        with sqlite3.connect((folder/'browser_history.sqlite').as_uri()+'?mode=ro',uri=True) as db:
            check('SQLite valid',db.execute('PRAGMA integrity_check').fetchone()==('ok',))
        for name in ('schema_guide.txt','case_context.txt'):
            (folder/name).read_text(encoding='utf-8'); check(name+' UTF-8',True)
        result=solve(folder)
    blobs.extend(p.read_bytes() for p in public.iterdir())
    check('literal final flag absent',all(result['flag'].encode() not in b and not re.search(rb'MT\{mt05_[0-9a-f]{16}\}',b) for b in blobs))
    check('private canonical value absent',all(result['canonical'].encode() not in b for b in blobs))
    patterns={
      'no credentials':rb'(?i)(password\s*[:=]|passwd\s*[:=]|BEGIN [A-Z ]*PRIVATE KEY)',
      'no CTFd secrets':rb'(?i)(SECRET_KEY\s*[:=]|ctfd_admin|DATABASE_URL\s*[:=]|REDIS_URL\s*[:=])',
      'no API tokens':rb'(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|(?i:api[_ -]?key\s*[:=]|bearer\s+[A-Za-z0-9._-]{16,}))',
    }
    for label,pattern in patterns.items(): check(label,not any(re.search(pattern,b) for b in blobs))
    check('release ready',True)
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); a=p.parse_args()
    try: validate(a.public)
    except (ValueError,OSError,zipfile.BadZipFile,sqlite3.Error) as error:
        print('[FAIL] '+str(error)); raise SystemExit(1)
