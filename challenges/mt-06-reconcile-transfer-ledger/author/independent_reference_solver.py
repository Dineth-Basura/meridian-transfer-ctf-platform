#!/usr/bin/env python3
"""Independent object-based implementation; does not import the other solver."""
import argparse
import base64
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Event:
    eid: str
    case: str
    record: str
    status: str
    utc: datetime
    token: bytes

    @staticmethod
    def parse(line):
        obj = json.loads(line)
        names = ['event_id', 'case_id', 'record_id', 'status', 'timestamp', 'token_b64']
        if type(obj) is not dict or any(type(obj.get(n)) is not str for n in names): raise ValueError('Schema')
        for n in names[:3]:
            s = obj[n]
            if not s or s[0] not in 'abcdefghijklmnopqrstuvwxyz' or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in s): raise ValueError('Identifier')
        stamp = obj['timestamp']
        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])', stamp): raise ValueError('Timestamp')
        time = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone.utc)
        raw = base64.b64decode(obj['token_b64'].encode('ascii'), validate=True)
        if base64.b64encode(raw).decode('ascii') != obj['token_b64']: raise ValueError('Base64')
        text = raw.decode('utf-8', errors='strict')
        if len(text) == 0 or any(c in text for c in ('\n', '\r')): raise ValueError('Token')
        return Event(obj['event_id'], obj['case_id'], obj['record_id'], obj['status'], time, raw)

def reconcile(lines, context):
    # Independently validate context using synthetic schema-valid records.
    if type(context) is not dict: raise ValueError('Context')
    allowed = context.get('allowed_record_ids')
    if type(allowed) is not list or not allowed or any(type(x) is not str for x in allowed) or len(set(allowed)) != len(allowed): raise ValueError('Allowed records')
    for record in allowed:
        Event.parse(json.dumps(dict(event_id='check', case_id=context.get('case_id'), record_id=record, status='completed', timestamp=context.get('start_utc'), token_b64='eA==')))
    times = []
    for key in ('start_utc', 'end_utc'):
        s = context.get(key)
        if type(s) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', s): raise ValueError('Context UTC')
        times.append(datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc))
    if times[0] >= times[1]: raise ValueError('Interval')
    records = []; rejected = total = 0
    for line in lines:
        total += 1
        try: records.append(Event.parse(line))
        except (ValueError, TypeError, UnicodeError): rejected += 1
    groups = {}
    for event in records: groups.setdefault(event.eid, []).append(event)
    unique = []
    candidates = 0
    for retries in groups.values():
        if len(set(retries)) != 1: raise ValueError('Conflicting duplicate event_id: dataset error')
        e = retries[0]
        if e.case == context['case_id'] and e.record in allowed and e.status == 'completed' and times[0] <= e.utc < times[1]:
            unique.append(e); candidates += len(retries)
    unique.sort(key=lambda e: (e.utc, e.eid))
    data = b'\x0a'.join(e.token for e in unique)
    digest = hashlib.sha256(data).hexdigest()
    selected = [dict(event_id=e.eid, record_id=e.record, utc_timestamp=e.utc.isoformat().replace('+00:00','Z'), token=e.token.decode('utf-8')) for e in unique]
    return dict(physical_rows=total, rejected_rows=rejected, candidate_rows=candidates, selected_count=len(unique), retries=candidates-len(unique), selected=selected, serialized_hex=data.hex(), serialized_length=len(data), sha256=digest, first32=digest[0:32], flag='MT{mt06_%s}' % digest[0:32])

def solve(public):
    data = (public/'mt06_ledger.zip').read_bytes()
    if (public/'SHA256SUMS').read_text().splitlines() != [hashlib.sha256(data).hexdigest()+'  mt06_ledger.zip']: raise ValueError('Outer checksum')
    names = {'events.jsonl','incident_context.json','schema.json','worked_example/example_events.jsonl','worked_example/example_context.json','worked_example/example_expected.txt'}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if len(archive.namelist()) != 7 or set(archive.namelist()) != {'meridian_mt06/'+n for n in names|{'EVIDENCE_SHA256SUMS'}}: raise ValueError('Archive inventory')
        blobs = {n:archive.read('meridian_mt06/'+n) for n in names}
        checks = archive.read('meridian_mt06/EVIDENCE_SHA256SUMS').decode().splitlines()
    if len(checks) != 6 or set(checks) != {hashlib.sha256(b).hexdigest()+'  '+n for n,b in blobs.items()}: raise ValueError('Inner checksum')
    return reconcile(blobs['events.jsonl'].decode('utf-8').splitlines(), json.loads(blobs['incident_context.json']))

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('public', nargs='?', type=Path, default=ROOT/'public'); p.add_argument('--details', action='store_true'); a=p.parse_args(); result=solve(a.public)
    if a.details: print(json.dumps(result, sort_keys=True))
    else:
        for k in ('physical_rows','rejected_rows','candidate_rows','selected_count'): print(k+': '+str(result[k]))
        print(result['flag'])
