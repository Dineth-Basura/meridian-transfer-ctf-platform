#!/usr/bin/env python3
"""Public-only procedural ledger solver; --details emits derived answer data."""
import argparse
import base64
import binascii
import hashlib
import json
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('events.jsonl', 'incident_context.json', 'schema.json', 'worked_example/example_events.jsonl', 'worked_example/example_context.json', 'worked_example/example_expected.txt')
FIELDS = ('event_id', 'case_id', 'record_id', 'status', 'timestamp', 'token_b64')
ID = r'[a-z][a-z0-9-]*'
STAMP = r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])'

def instant(value):
    if not isinstance(value, str) or not re.fullmatch(STAMP, value):
        raise ValueError('Expected offset-aware ISO 8601 exact seconds')
    return datetime.fromisoformat(value).astimezone(timezone.utc)

def context_valid(context):
    if not isinstance(context, dict) or not isinstance(context.get('case_id'), str) or not re.fullmatch(ID, context['case_id']):
        raise ValueError('Invalid context case')
    allowed = context.get('allowed_record_ids')
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) or not re.fullmatch(ID, x) for x in allowed) or len(set(allowed)) != len(allowed):
        raise ValueError('Invalid allowed records')
    start, end = (instant(context.get(k)) for k in ('start_utc', 'end_utc'))
    if not context['start_utc'].endswith('Z') or not context['end_utc'].endswith('Z') or start >= end:
        raise ValueError('Invalid UTC interval')
    return start, end

def reconcile(lines, context):
    start, end = context_valid(context)
    selected, seen = {}, {}
    rejected = candidates = physical = 0
    for line in lines:
        physical += 1
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in FIELDS):
                raise ValueError('Required string fields')
            if any(not re.fullmatch(ID, row[k]) for k in FIELDS[:3]):
                raise ValueError('Invalid identifier')
            utc = instant(row['timestamp'])
            token_bytes = base64.b64decode(row['token_b64'], validate=True)
            if base64.b64encode(token_bytes).decode('ascii') != row['token_b64']:
                raise ValueError('Noncanonical Base64')
            token = token_bytes.decode('utf-8')
            if not token or '\r' in token or '\n' in token:
                raise ValueError('Token must be nonempty and contain no CR/LF')
        except (ValueError, TypeError, binascii.Error, UnicodeError):
            rejected += 1
            continue
        # Every schema-valid duplicate is checked, including excluded records.
        semantic = (row['case_id'], row['record_id'], row['status'], utc, token_bytes)
        eid = row['event_id']
        if eid in seen and seen[eid] != semantic:
            raise ValueError('Conflicting duplicate event_id: dataset error')
        seen[eid] = semantic
        if row['case_id'] == context['case_id'] and row['record_id'] in context['allowed_record_ids'] and row['status'] == 'completed' and start <= utc < end:
            candidates += 1
            selected[eid] = dict(event_id=eid, record_id=row['record_id'], utc_timestamp=utc.strftime('%Y-%m-%dT%H:%M:%SZ'), token=token)
    ordered = sorted(selected.values(), key=lambda r: (r['utc_timestamp'], r['event_id']))
    serialized = '\n'.join(r['token'] for r in ordered).encode('utf-8')
    digest = hashlib.sha256(serialized).hexdigest()
    return dict(physical_rows=physical, rejected_rows=rejected, candidate_rows=candidates, selected_count=len(ordered), retries=candidates-len(ordered), selected=ordered, serialized_hex=serialized.hex(), serialized_length=len(serialized), sha256=digest, first32=digest[:32], flag='MT{mt06_'+digest[:32]+'}')

def verify_manifest(folder, name, expected):
    rows = (folder/name).read_text('utf-8').splitlines()
    wanted = [hashlib.sha256((folder/n).read_bytes()).hexdigest()+'  '+n for n in expected]
    if len(rows) != len(wanted) or set(rows) != set(wanted):
        raise ValueError('Checksum or manifest inventory mismatch')

def unpack(public, destination):
    verify_manifest(public, 'SHA256SUMS', ['mt06_ledger.zip'])
    with zipfile.ZipFile(public/'mt06_ledger.zip') as z:
        expected = {'meridian_mt06/'+n for n in (*FILES, 'EVIDENCE_SHA256SUMS')}
        if len(z.namelist()) != len(expected) or set(z.namelist()) != expected:
            raise ValueError('Unsafe archive inventory')
        z.extractall(destination)
    folder = destination/'meridian_mt06'
    verify_manifest(folder, 'EVIDENCE_SHA256SUMS', FILES)
    return folder

def solve(public):
    with tempfile.TemporaryDirectory() as tmp:
        folder = unpack(public, Path(tmp))
        context = json.loads((folder/'incident_context.json').read_text('utf-8'))
        with (folder/'events.jsonl').open(encoding='utf-8', newline='') as f:
            return reconcile(f, context)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('public', nargs='?', type=Path, default=ROOT/'public'); parser.add_argument('--details', action='store_true'); args = parser.parse_args()
    result = solve(args.public)
    if args.details: print(json.dumps(result, sort_keys=True))
    else:
        for key in ('physical_rows', 'rejected_rows', 'candidate_rows', 'selected_count'): print(key+': '+str(result[key]))
        print(result['flag'])
