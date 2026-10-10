#!/usr/bin/env python3
"""Validate public evidence, independent solver agreement and author invariants."""
import argparse
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from reference_solver import ROOT, unpack, reconcile, instant, context_valid, solve
from independent_reference_solver import solve as independent

def validate(public, compare_private=None):
    with tempfile.TemporaryDirectory() as tmp:
        folder=unpack(public,Path(tmp)); data=(folder/'events.jsonl').read_bytes()
        if data.count(b'\n')!=1000 or not data.endswith(b'\n') or b'\r' in data: raise ValueError('Physical row invariant')
        ctx=json.loads((folder/'incident_context.json').read_text()); start,end=context_valid(ctx)
        result=reconcile(data.decode('utf-8').splitlines(),ctx)
        if result!=independent(public): raise ValueError('Independent intermediate disagreement')
        if result!=solve(public): raise ValueError('Repeat nondeterminism')
        if (result['selected_count'],result['rejected_rows'],result['retries'])!=(20,414,8): raise ValueError('Author composition')
        selected=result['selected']; times=[instant(r['utc_timestamp']) for r in selected]
        if start not in times or (end-start).total_seconds()!=10800 or end in times: raise ValueError('Boundary semantics')
        if not any((end-t).total_seconds()==1 for t in times): raise ValueError('Before-end fixture')
        if max(Counter(times).values())<2: raise ValueError('Missing tie')
        offsets=set(); raw_times=[]
        selected_ids={r['event_id'] for r in selected}
        for line in data.decode().splitlines():
            try: row=json.loads(line)
            except ValueError: continue
            if isinstance(row,dict) and isinstance(row.get('timestamp'),str):
                try: raw_times.append(instant(row['timestamp']))
                except ValueError: pass
                if row.get('event_id') in selected_ids: offsets.add(row['timestamp'][-6:] if not row['timestamp'].endswith('Z') else 'Z')
        if offsets!={'Z','+05:30','+02:00','-04:00'}: raise ValueError('Offset coverage')
        if end not in raw_times or not any((start-t).total_seconds()==1 for t in raw_times): raise ValueError('Missing excluded boundary fixtures')
        if not re.fullmatch(r'MT\{mt06_[0-9a-f]{32}\}',result['flag']): raise ValueError('Flag format')
        if compare_private:
            if json.loads((compare_private/'expected_selection.json').read_text())!=result: raise ValueError('Private selection mismatch')
            if (compare_private/'expected_serialization.bin').read_bytes()!=bytes.fromhex(result['serialized_hex']): raise ValueError('Private byte mismatch')
            if (compare_private/'flag.txt').read_text().strip()!=result['flag']: raise ValueError('Private flag mismatch')
        return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); a=p.parse_args()
    validate(a.public); print('PASS: dataset, boundaries, offsets, retries, deterministic bytes and complete solver agreement')
