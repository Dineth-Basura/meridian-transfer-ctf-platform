#!/usr/bin/env python3
"""Public-only dictionary-based forensic solver. --details emits author answers."""
import argparse
import csv
import hashlib
import json
import locale
import re
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

locale.setlocale(locale.LC_TIME, 'C')

ROOT = Path(__file__).resolve().parents[1]
FILES = ('web_access.log','application_audit.csv','browser_history.sqlite','schema_guide.txt','case_context.txt')
HEADERS = ['event_id','record_id','user_id','action','status','application_time','source']
LOG = re.compile(r'^(?P<session>[a-z0-9-]+) \[(?P<time>[^]]+)\] "(?P<method>GET|POST) (?P<route>/[^ ]+) HTTP/1.1" (?P<status>\d{3}) (?P<size>\d+) event=(?P<event>[a-z0-9-]+) record=(?P<record>[a-z0-9-]+)$')

def verify_manifest(folder, manifest, expected):
    lines=(folder/manifest).read_text(encoding='utf-8').splitlines()
    entries={}
    for line in lines:
        match=re.fullmatch(r'([0-9a-f]{64})  ([a-zA-Z0-9_.]+)',line)
        if not match or match[2] in entries: raise ValueError('Invalid manifest')
        entries[match[2]]=match[1]
    if set(entries)!=set(expected): raise ValueError('Manifest inventory mismatch')
    for name,digest in entries.items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest: raise ValueError('Evidence checksum mismatch')

def unpack(public, destination):
    verify_manifest(public,'SHA256SUMS',['mt05_evidence.zip'])
    with zipfile.ZipFile(public/'mt05_evidence.zip') as z:
        expected={'meridian_mt05/'+n for n in (*FILES,'EVIDENCE_SHA256SUMS')}
        if len(z.namelist())!=len(expected) or set(z.namelist())!=expected: raise ValueError('Unsafe archive inventory')
        z.extractall(destination)
    folder=destination/'meridian_mt05'
    verify_manifest(folder,'EVIDENCE_SHA256SUMS',FILES)
    return folder

def application_time(value):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}',value): raise ValueError('Offset seconds required')
    return datetime.fromisoformat(value).astimezone(timezone.utc)

def canonical(event, instant, record):
    for value in (event,record):
        if not re.fullmatch(r'[a-z][a-z0-9-]*',value,flags=re.ASCII): raise ValueError('Lowercase ASCII identifier required')
    if instant.tzinfo is None or instant.utcoffset().total_seconds()!=0 or instant.microsecond: raise ValueError('UTC exact seconds required')
    timestamp=instant.strftime('%Y-%m-%dT%H:%M:%SZ')
    value=f'{event}|{timestamp}|{record}'
    if not re.fullmatch(r'[a-z][a-z0-9-]*\|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\|[a-z][a-z0-9-]*',value,flags=re.ASCII): raise ValueError('Invalid canonical serialization')
    if value.strip()!=value or any(c.isspace() for c in value) or value.count('|')!=2: raise ValueError('Whitespace or separators')
    encoded=value.encode('utf-8')
    if encoded.decode('utf-8')!=value or b'\r' in encoded or b'\n' in encoded: raise ValueError('Encoding ambiguity')
    digest=hashlib.sha256(encoded).hexdigest()
    if not re.fullmatch('[0-9a-f]{64}',digest): raise ValueError('Invalid digest')
    first16=digest[:16]
    if not re.fullmatch('[0-9a-f]{16}',first16): raise ValueError('Invalid truncation')
    return dict(event_id=event,utc_timestamp=timestamp,record_id=record,canonical=value,canonical_utf8_hex=encoded.hex(),sha256=digest,first16=first16,flag='MT{mt05_'+first16+'}')

def load(folder):
    verify_manifest(folder,'EVIDENCE_SHA256SUMS',FILES)
    context=dict(line.split('=',1) for line in (folder/'case_context.txt').read_text().splitlines() if '=' in line)
    guide=(folder/'schema_guide.txt').read_text(encoding='utf-8')
    for required in ('Unix epoch milliseconds','YYYY-MM-DD HH:MM:SS+05:30','absolute time difference <= 60 seconds'):
        if required not in guide: raise ValueError('Unsupported schema')
    with (folder/'application_audit.csv').open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=HEADERS: raise ValueError('CSV schema')
        audit=list(reader)
    web=[]
    for line in (folder/'web_access.log').read_text().splitlines():
        m=LOG.fullmatch(line)
        if not m: raise ValueError('Invalid access row')
        row=m.groupdict(); row['instant']=datetime.strptime(row['time'],'%d/%b/%Y:%H:%M:%S %z'); web.append(row)
    with sqlite3.connect((folder/'browser_history.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',): raise ValueError('SQLite integrity')
        visits=db.execute('SELECT id,url,title,visit_time,visit_type FROM visits').fetchall()
    return context,audit,web,visits

def select(context,audit,web,visits):
    start=datetime.fromisoformat(context['window_start']); end=datetime.fromisoformat(context['window_end'])
    results=[]
    for row in audit:
        instant=application_time(row['application_time'])
        if not (start<=instant<end and row['action']=='export' and row['status']=='completed' and row['record_id'].startswith(context['restricted_prefix'])): continue
        matching=[w for w in web if w['event']==row['event_id'] and w['record']==row['record_id'] and w['route']=='/export/'+row['record_id'] and w['method']=='GET' and w['status']=='200' and w['instant']==instant]
        if not matching: continue
        for _,url,_,millis,kind in visits:
            u=urlparse(url); q=parse_qs(u.query)
            if (u.scheme=='http' and u.netloc=='mt04.lab.invalid' and u.path=='/export/'+row['record_id'] and q=={'event':[row['event_id']]} and kind=='export' and abs(millis-int(instant.timestamp())*1000)<=60000):
                results.append(row); break
    return results

def solve(folder):
    rows=select(*load(folder))
    if len(rows)!=1: raise ValueError('Expected exactly one qualifying event')
    r=rows[0]
    return canonical(r['event_id'],application_time(r['application_time']),r['record_id'])

def main():
    p=argparse.ArgumentParser(); p.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); p.add_argument('--details',action='store_true'); args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        result=solve(unpack(args.public,Path(tmp)))
    print(json.dumps(result,sort_keys=True) if args.details else result['flag'])
if __name__=='__main__': main()
