#!/usr/bin/env python3
"""Independent SQL-join solver; no imports from builder or main solver."""
import argparse
import csv
import hashlib
import io
import json
import locale
import re
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl

locale.setlocale(locale.LC_TIME, 'C')

ROOT=Path(__file__).resolve().parents[1]

def serialize(event,timestamp,record):
    for identifier in (event,record):
        if not identifier or identifier[0] not in 'abcdefghijklmnopqrstuvwxyz' or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in identifier): raise ValueError('Identifier must be lowercase ASCII')
    if len(timestamp)!=20 or timestamp[-1]!='Z': raise ValueError('UTC second representation required')
    instant=datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    if instant.isoformat(timespec='seconds').replace('+00:00','Z')!=timestamp: raise ValueError('Noncanonical time')
    text='|'.join((event,timestamp,record))
    if text.count('|')!=2 or any(c.isspace() for c in text) or '\r' in text or '\n' in text or text!=text.strip(): raise ValueError('Invalid bytes')
    data=text.encode('utf-8','strict')
    digest=hashlib.sha256(data).hexdigest()
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest): raise ValueError('Digest format')
    short=''.join(digest[i] for i in range(16))
    if len(short)!=16: raise ValueError('Truncation')
    return {'event_id':event,'utc_timestamp':timestamp,'record_id':record,'canonical':text,'canonical_utf8_hex':data.hex(),'sha256':digest,'first16':short,'flag':'MT{mt05_'+short+'}'}

def solve(public):
    archive=(public/'mt05_evidence.zip').read_bytes()
    line=(public/'SHA256SUMS').read_text().splitlines()
    if line!=[hashlib.sha256(archive).hexdigest()+'  mt05_evidence.zip']: raise ValueError('Outer integrity')
    names={'web_access.log','application_audit.csv','browser_history.sqlite','schema_guide.txt','case_context.txt'}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if len(z.infolist())!=6 or set(z.namelist())!={'meridian_mt05/'+x for x in names|{'EVIDENCE_SHA256SUMS'}}: raise ValueError('Archive inventory')
        blobs={n:z.read('meridian_mt05/'+n) for n in names}
        checks=z.read('meridian_mt05/EVIDENCE_SHA256SUMS').decode().splitlines()
    expected={hashlib.sha256(data).hexdigest()+'  '+name for name,data in blobs.items()}
    if len(checks)!=5 or set(checks)!=expected: raise ValueError('Inner integrity')
    context={}
    for line in blobs['case_context.txt'].decode().splitlines():
        if '=' in line:
            key,_,value=line.partition('='); context[key]=value
    guide=blobs['schema_guide.txt'].decode('utf-8')
    if not all(s in guide for s in ('Unix epoch milliseconds','YYYY-MM-DD HH:MM:SS+05:30','absolute time difference <= 60 seconds')): raise ValueError('Unknown time schema')
    db=sqlite3.connect(':memory:')
    db.executescript('CREATE TABLE audit(event TEXT, record TEXT, action TEXT, status TEXT, epoch INTEGER); CREATE TABLE web(event TEXT,record TEXT,epoch INTEGER); CREATE TABLE browser(event TEXT,record TEXT,ms INTEGER);')
    reader=csv.DictReader(io.StringIO(blobs['application_audit.csv'].decode()))
    if reader.fieldnames!=['event_id','record_id','user_id','action','status','application_time','source']: raise ValueError('Audit schema')
    for row in reader:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}',row['application_time']): raise ValueError('Timestamp precision')
        dt=datetime.strptime(row['application_time'],'%Y-%m-%d %H:%M:%S%z')
        db.execute('INSERT INTO audit VALUES (?,?,?,?,?)',(row['event_id'],row['record_id'],row['action'],row['status'],int(dt.timestamp())))
    for line in blobs['web_access.log'].decode().splitlines():
        left,request,right=line.split('"')
        stamp=left.split('[',1)[1].split(']',1)[0]
        method,route,protocol=request.split(); code,size,event,record=right.split()
        eid=event.removeprefix('event='); rid=record.removeprefix('record=')
        if method=='GET' and code=='200' and route=='/export/'+rid:
            epoch=int(datetime.strptime(stamp,'%d/%b/%Y:%H:%M:%S %z').timestamp())
            db.execute('INSERT INTO web VALUES (?,?,?)',(eid,rid,epoch))
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'history.sqlite'; path.write_bytes(blobs['browser_history.sqlite'])
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as history:
            if history.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('SQLite integrity')
            for url,ms,kind in history.execute('SELECT url,visit_time,visit_type FROM visits'):
                parts=urlsplit(url); query=parse_qsl(parts.query)
                if kind=='export' and parts.scheme=='http' and parts.netloc=='mt04.lab.invalid' and parts.path.startswith('/export/') and len(query)==1 and query[0][0]=='event':
                    db.execute('INSERT INTO browser VALUES (?,?,?)',(query[0][1],parts.path[len('/export/'):],ms))
    bounds=[int(datetime.strptime(context[k],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()) for k in ('window_start','window_end')]
    rows=db.execute('''SELECT DISTINCT a.event,a.record,a.epoch FROM audit a
       JOIN web w ON a.event=w.event AND a.record=w.record AND a.epoch=w.epoch
       JOIN browser b ON a.event=b.event AND a.record=b.record
       WHERE a.action='export' AND a.status='completed' AND substr(a.record,1,?)=?
       AND a.epoch>=? AND a.epoch<? AND abs(b.ms-a.epoch*1000)<=60000''',(len(context['restricted_prefix']),context['restricted_prefix'],*bounds)).fetchall()
    db.close()
    if len(rows)!=1: raise ValueError('Expected one qualifying event')
    event,record,epoch=rows[0]
    timestamp=datetime.fromtimestamp(epoch,timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    return serialize(event,timestamp,record)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('public',nargs='?',type=Path,default=ROOT/'public'); parser.add_argument('--details',action='store_true'); args=parser.parse_args()
    result=solve(args.public); print(json.dumps(result,sort_keys=True) if args.details else result['flag'])
