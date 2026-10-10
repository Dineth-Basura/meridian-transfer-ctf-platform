#!/usr/bin/env python3
"""Inspect public/ only, including derived-answer leak checks."""
import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from reference_solver import ROOT, FILES, unpack, reconcile, context_valid

def validate(public,verbose=True):
    def check(label,condition):
        if not condition: raise ValueError(label)
        if verbose: print('[PASS] '+label)
    check('expected public files present',{p.name for p in public.iterdir()}=={'README.txt','SHA256SUMS','mt06_ledger.zip'})
    with zipfile.ZipFile(public/'mt06_ledger.zip') as z:
        check('ZIP valid',z.testzip() is None)
        names=z.namelist()
        check('no path traversal',all('..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
        check('no absolute paths',all(not PurePosixPath(n).is_absolute() and ':' not in n for n in names))
        check('expected inner files',len(names)==7 and set(names)=={'meridian_mt06/'+n for n in (*FILES,'EVIDENCE_SHA256SUMS')})
        check('deterministic archive format',names==sorted(names) and not z.comment and all(i.date_time==(2026,10,17,0,0,0) and i.create_system==3 and i.external_attr==0o100644<<16 and i.compress_type==zipfile.ZIP_DEFLATED and not i.extra and not i.comment for i in z.infolist()))
        blobs=[z.read(n) for n in names]
        production=[z.read(n) for n in names if '/worked_example/' not in n]
    with tempfile.TemporaryDirectory() as tmp:
        folder=unpack(public,Path(tmp))
        check('outer SHA256 manifest valid',True); check('inner SHA256 manifest valid',True)
        data=(folder/'events.jsonl').read_bytes()
        check('events.jsonl has exactly 1000 physical rows',data.count(b'\n')==1000 and data.endswith(b'\n') and b'\r' not in data)
        ctx=json.loads((folder/'incident_context.json').read_text()); context_valid(ctx); check('context valid',True)
        schema=json.loads((folder/'schema.json').read_text())
        check('schema valid',schema['required']=={k:'string' for k in ('event_id','case_id','record_id','status','timestamp','token_b64')} and schema['qualifying_status']=='completed' and 'FIRST 32' in schema['derivation_contract'])
        toy=reconcile((folder/'worked_example/example_events.jsonl').read_text().splitlines(),json.loads((folder/'worked_example/example_context.json').read_text()))
        check('worked example present',toy['flag'] in (folder/'worked_example/example_expected.txt').read_text())
        result=reconcile(data.decode().splitlines(),ctx)
    all_blobs=blobs+[p.read_bytes() for p in public.iterdir()]
    check('no literal final flag',all(result['flag'].encode() not in b for b in all_blobs))
    # Toy result is explicitly allowed; production answer structures are forbidden.
    check('no private selected-event data',all(b'"selected"' not in b and b'"serialized_hex"' not in b for b in production) and all(bytes.fromhex(result['serialized_hex']) not in b for b in all_blobs))
    check('no answer sheet',not any(any(s in n for s in ('private','solution','expected_selection','expected_serialization','author','.py')) for n in names))
    for label,pattern in [('no credentials',rb'(?i)(password\s*[:=]|passwd\s*[:=]|BEGIN [A-Z ]*PRIVATE KEY)'),('no CTFd secret',rb'(?i)(SECRET_KEY\s*[:=]|ctfd_admin|DATABASE_URL\s*[:=]|REDIS_URL\s*[:=])'),('no API token',rb'(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|(?i:api[_ -]?key\s*[:=]|bearer\s+[A-Za-z0-9._-]{16,}))')]:
        check(label,not any(re.search(pattern,b) for b in all_blobs))
    check('release ready',True)
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); a=p.parse_args()
    try: validate(a.public)
    except (ValueError,OSError,KeyError,zipfile.BadZipFile) as e: print('[FAIL] '+str(e)); raise SystemExit(1)
