#!/usr/bin/env python3
"""Deterministic offline authoring. Never print production answers."""
import base64
import hashlib
import json
import random
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from reference_solver import ROOT, FILES, reconcile

SOURCE = 'MERIDIAN-MT06-V1'
CONTRACT = '''Parse events.jsonl line-by-line as UTF-8. There are exactly 1000 physical
rows, including intentionally malformed JSON and schema-invalid records.
Count and skip invalid rows; validate ALL rows before filtering. Required fields
are strings: event_id, case_id, record_id, status, timestamp, token_b64.
Identifiers match [a-z][a-z0-9-]* (ASCII). Extra fields are ignored.
Timestamps use YYYY-MM-DDTHH:MM:SS followed by Z or +/-HH:MM; hours 00–23,
offset minutes 00–59, exact seconds, valid calendar date, no naive times,
fractional seconds or leap seconds. Normalize to UTC.
token_b64 uses canonical standard RFC 4648 Base64 with required padding,
strict alphabet validation, and no whitespace. Re-encoding decoded bytes must
match the original. Bytes must decode as UTF-8. Tokens are nonempty and contain
no CR or LF. Preserve all other token characters, including any spaces.
Validate duplicate event_id values across ALL schema-valid rows. Their semantic
values (case_id, record_id, status, normalized timestamp, token bytes) must agree.
An equivalent timestamp offset is not a conflict. Ignore invalid rows for this
check. Any conflicting duplicate is a fatal DATASET ERROR; never choose one.
Select rows only when case_id exactly matches incident_context.json, record_id
is in allowed_record_ids, status is exactly completed, and normalized time is
>= start_utc AND < end_utc (start inclusive, end exclusive).
Collapse identical qualifying retries by event_id BEFORE final sorting.
Sort by normalized UTC timestamp ascending, THEN event_id ascending using ASCII
ordering. Decode selected tokens and join the token strings with one LF (0x0A)
between adjacent tokens. Do not strip tokens, add spaces, include event IDs,
serialize JSON, use CRLF, or append a final LF. Encode the result as UTF-8.
Compute SHA-256; use the FIRST 32 lowercase hexadecimal digest characters.
Submit MT{mt06_<digest32>}. An empty toy selection hashes empty bytes; the
production dataset is guaranteed to have a nonempty selection.
No earlier stage secret is required. All context is supplied locally.
'''
README = '''Stage: MT-06
Title: Reconcile the Transfer Ledger
Domain: Programming / Scripting
Difficulty: Hard
Estimated solve time: 40–60 minutes
Objective: Write a reproducible parser that validates the supplied JSONL transfer
ledger, filters incident events, handles retries, normalizes time, decodes tokens
and derives a deterministic final flag.
Files: mt06_ledger.zip, SHA256SUMS
Suggested tools: Python 3, text editor, sha256sum, unzip; optional jq.
Internet required: No. All evidence is synthetic and offline.
Flag format: MT{mt06_<32 lowercase hex>}
Verify: sha256sum -c SHA256SUMS
Extract: unzip mt06_ledger.zip
Then inside meridian_mt06: sha256sum -c EVIDENCE_SHA256SUMS
Read schema.json and incident_context.json. The worked_example directory shows
a toy calculation only. Preserve originals and work on a disposable copy.

'''+CONTRACT
HINTS = ['Separate parsing, validation, filtering and output construction. Count rejected rows rather than allowing one bad line to terminate the whole analysis.', 'Deduplicate by event_id before final sorting. Sort by normalized UTC time then event_id, and check the exact no-final-newline serialization rule.']

def context():
    return dict(source=SOURCE, case_id='meridian-transfer-review', allowed_record_ids=['ledger-north','ledger-east','ledger-west','ledger-south'], start_utc='2026-10-17T08:00:00Z', end_utc='2026-10-17T11:00:00Z')

def event(eid, seconds=60, token='Synthetic fragment', offset=0, **updates):
    t = datetime(2026,10,17,8,tzinfo=timezone.utc)+timedelta(seconds=seconds)
    stamp = t.astimezone(timezone(timedelta(minutes=offset))).isoformat().replace('+00:00','Z')
    row = dict(event_id=eid, case_id=context()['case_id'], record_id='ledger-north', status='completed', timestamp=stamp, token_b64=base64.b64encode(token.encode('utf-8')).decode('ascii'))
    row.update(updates)
    return row

def encode(rows):
    return ''.join((r if isinstance(r,str) else json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')))+'\n' for r in rows).encode('utf-8')

def production():
    rng = random.Random(SOURCE)
    ids = rng.sample(range(10000,99999),1000)
    rows=[]
    times=[0,10799,1800,1800]+[240+i*431 for i in range(16)]
    for i,secs in enumerate(times):
        token='Transfer/%s:%s' % (hashlib.sha256((SOURCE+str(i)).encode()).hexdigest()[:13], ['Ready','café','Review','Δelta'][i%4])
        rows.append(event('ev-'+str(ids[i]), secs, token, [0,330,120,-240][i%4], record_id=context()['allowed_record_ids'][i%4]))
    for i in range(8): rows.append(dict(rows[i]))
    # Explicit one-second-before-start and exact-end exclusions.
    rows.extend([event('ev-'+str(ids[20]),-1),event('ev-'+str(ids[21]),10800)])
    for i in range(22,992):
        row=event('ev-'+str(ids[i]),60+(i*137)%10000,'Archive note '+str(i),[0,330,120,-240][i%4])
        category=(i-22)%14
        if category==0: row['case_id']='other-review'
        elif category==1: row['record_id']='unrelated-file'
        elif category in (2,3,4): row['status']=['failed','pending','cancelled'][category-2]
        elif category==5: row['timestamp']='2026-10-17T07:59:59Z'
        elif category==6: row['timestamp']='2026-10-17T11:00:01Z'
        elif category==7: row['token_b64']='invalid!'
        elif category==8: row='{"event_id":'
        elif category==9: del row['record_id']
        elif category==10: row['status']=42
        elif category==11: row['timestamp']='2026-10-17T09:00:00'
        elif category==12: row['token_b64']='/w=='
        else: row['case_id']='archive-background'
        rows.append(row)
    assert len(rows)==1000
    rng.shuffle(rows)
    # Make ignoring the secondary sort observably wrong, independently of RNG changes.
    tied={r['event_id'] for r in rows if isinstance(r,dict) and r.get('event_id') in {'ev-'+str(ids[2]),'ev-'+str(ids[3])}}
    positions=[i for i,r in enumerate(rows) if isinstance(r,dict) and r.get('event_id') in tied]
    tied_rows=sorted([rows[i] for i in positions],key=lambda r:r['event_id'],reverse=True)
    for pos,row in zip(positions,tied_rows): rows[pos]=row
    return encode(rows)

def toy():
    rows=[event('toy-c',1800,'Gamma',120),event('toy-b',1800,'Beta',-240),event('toy-a',0,'Alpha',330),event('toy-a',0,'Alpha',330),event('toy-f',200,'Ignored',status='failed'),event('toy-x',10800,'Excluded'),event('toy-w',100,'Other',case_id='other-case'),'{broken',event('toy-n',50,'Bad',token_b64='!')]
    return encode(rows)

def manifest(blobs):
    return ''.join(hashlib.sha256(blobs[n]).hexdigest()+'  '+n+'\n' for n in sorted(blobs)).encode()

def build(root=ROOT):
    public,private=root/'public',root/'private'
    public.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)
    data=production(); ctx=context()
    result=reconcile(data.decode().splitlines(),ctx)
    from independent_reference_solver import reconcile as independent
    if result != independent(data.decode().splitlines(),ctx): raise ValueError('Build solver disagreement')
    if (result['physical_rows'],result['selected_count'],result['rejected_rows'],result['retries']) != (1000,20,414,8): raise ValueError('Production composition invariant')
    schema=dict(source=SOURCE, required={k:'string' for k in ('event_id','case_id','record_id','status','timestamp','token_b64')}, identifier_pattern='[a-z][a-z0-9-]*', qualifying_status='completed', derivation_contract=CONTRACT)
    toy_data=toy(); toy_result=reconcile(toy_data.decode().splitlines(),ctx)
    expected='TOY ONLY — not the production answer\n'+json.dumps(toy_result,indent=2,ensure_ascii=False)+'\nSerialization text (escaped): '+json.dumps(bytes.fromhex(toy_result['serialized_hex']).decode())+'\nNo final LF in hashed bytes.\n'
    blobs={'events.jsonl':data,'incident_context.json':(json.dumps(ctx,indent=2)+'\n').encode(),'schema.json':(json.dumps(schema,indent=2)+'\n').encode(),'worked_example/example_events.jsonl':toy_data,'worked_example/example_context.json':(json.dumps(ctx,indent=2)+'\n').encode(),'worked_example/example_expected.txt':expected.encode('utf-8')}
    blobs['EVIDENCE_SHA256SUMS']=manifest(blobs)
    with zipfile.ZipFile(public/'mt06_ledger.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(blobs):
            info=zipfile.ZipInfo('meridian_mt06/'+name,(2026,10,17,0,0,0)); info.create_system=3; info.external_attr=0o100644<<16; info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,blobs[name],compresslevel=9)
    (public/'SHA256SUMS').write_bytes(manifest({'mt06_ledger.zip':(public/'mt06_ledger.zip').read_bytes()}))
    (public/'README.txt').write_text(README,encoding='utf-8')
    (private/'expected_selection.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (private/'expected_serialization.bin').write_bytes(bytes.fromhex(result['serialized_hex']))
    (private/'flag.txt').write_text(result['flag']+'\n')
    spec=(ROOT/'docs/MT06_SPECIFICATION.md').read_text() if (ROOT/'docs/MT06_SPECIFICATION.md').exists() else README
    (private/'solution.md').write_text(spec+'\n\n## Private solution\n'+CONTRACT+'\nUse streaming JSONL parsing with robust exceptions. Validate before filtering; normalize timezone-aware datetime values; compare semantic duplicate tuples; sort deterministically and hash exact UTF-8 bytes. Empty toy selections are allowed, but production must be nonempty.\n\n'+json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (private/'challenge_config.md').write_text('Stage: MT-06\nName: Reconcile the Transfer Ledger\nCategory: Programming / Scripting\nDifficulty: Hard\nValue: 400\nType: standard/static\nState: visible\nFlag provider: static/exact\nDynamic scoring: disabled\nPrerequisite: none\nAttachments: mt06_ledger.zip, SHA256SUMS\nFlag: '+result['flag']+'\nHints: two free hints (0, 0)\n'+'\n'.join(HINTS)+'\n')
    from validate_dataset import validate
    validate(public,compare_private=private)
    return result

if __name__=='__main__':
    build(); print('PASS: deterministic 1000-row ledger built; private answers written')
