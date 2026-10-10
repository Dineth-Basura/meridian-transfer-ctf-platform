#!/usr/bin/env python3
"""Deterministic MERIDIAN-MT05-V1 source; author answers never printed."""
import csv
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from reference_solver import FILES, HEADERS, solve, select, load

ROOT=Path(__file__).resolve().parents[1]
SOURCE='MERIDIAN-MT05-V1'
RULE='''Canonical value: event_id|YYYY-MM-DDTHH:MM:SSZ|record_id
Use the normalized application audit timestamp in UTC with exact seconds,
lowercase ASCII event_id and record_id, uppercase literal Z, literal | separators,
no spaces, no surrounding whitespace, no CR or LF, and no trailing newline.
Encode the canonical value as UTF-8 bytes. Compute SHA-256 and take exactly
the first 16 lowercase hexadecimal characters. Submit MT{mt05_<digest16>}.
'''
CONTEXT='''Case reference: MERIDIAN-MT05-V1
All evidence is fictional and synthetic. No previous stage flag is required.
The export portal and a synthetic analyst workstation appear to disagree about
when a restricted handover occurred. Reconstruct the one completed restricted
export supported by all three sources; retries and unrelated work are present.
window_start=2026-10-17T08:00:00Z
window_end=2026-10-17T11:00:00Z
restricted_prefix=rst-
Window is start inclusive, end exclusive, evaluated using application UTC time.
A qualifying row has action export and status completed for the restricted family.
Require a GET /export/<record_id> web entry with HTTP 200, matching event_id,
record_id, and exactly the same normalized timestamp as the application event.
Require browser visit_type export, the same record in the /export/ URL path and
the same event in its event query parameter on http://mt04.lab.invalid.
Browser corroboration uses absolute time difference <= 60 seconds, inclusive,
relative to the normalized application event; visits may precede or follow it.
A 200 normal view is not an export. An audit completion alone is insufficient.
Exactly one event meets every condition. Preserve originals; analyze working copies.
'''+RULE
GUIDE='''MERIDIAN-MT05-V1 evidence schema (all records synthetic)
web_access.log: session [timestamp] "method route HTTP/1.1" status bytes event=ID record=ID
Timestamp: DD/Mon/YYYY:HH:MM:SS +0000, UTC; English month abbreviations.
Sessions are fictional source labels, not IP addresses or credentials.
HTTP 200 denotes success; 403/500 denote failure. GET /release/ is a normal view;
GET /export/ is an export. IDs must match across sources, not just nearby times.
application_audit.csv: UTF-8 CSV with columns event_id,record_id,user_id,action,
status,application_time,source. Identifiers are lowercase ASCII; user_id is a
synthetic alias. source identifies the synthetic data collection source.
action: export or view. status: completed, failed, cancelled. Only completed
export qualifies. application_time: YYYY-MM-DD HH:MM:SS+05:30, explicit fixed
UTC offset +05:30, not a local machine timezone. Subtract 5 hours 30 minutes
for UTC, carrying dates as necessary; timestamps have exact seconds precision.
browser_history.sqlite: SQLite 3; table visits:
id INTEGER PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL,
visit_time INTEGER NOT NULL, visit_type TEXT NOT NULL.
visit_time is Unix epoch milliseconds since 1970-01-01T00:00:00Z (UTC), not
seconds or microseconds. visit_type is export or navigation. All URLs use the
reserved fictional host mt04.lab.invalid. event query parameter is an event ID.
Browser correlation: absolute time difference <= 60 seconds (inclusive).
Case window and all selection criteria are in case_context.txt.
EVIDENCE_SHA256SUMS lists SHA-256 of the five original evidence/context files.
Verify hashes before analysis. Preserve originals. Work on a copy:
cp browser_history.sqlite browser_history_working.sqlite
Or open with sqlite3 URI file:browser_history.sqlite?mode=ro.
Do not modify the original SQLite file or expect real browser-specific tables.
'''
README='''Stage: MT-05
Title: The Offset in the Handover Log
Domain: Digital Forensics
Difficulty: Moderate-Hard
Estimated solve time: 30–45 minutes
Objective: Preserve and inspect the supplied forensic evidence, normalize
timestamps, correlate the three independent sources, identify the single
completed restricted export, and derive the stage flag.
Files: mt05_evidence.zip, SHA256SUMS
Suggested tools: sha256sum, file, unzip, grep, Python 3, sqlite3, CSV tools;
optional jq. Internet required: No.
Flag format: MT{mt05_<16 lowercase hex>}
Verify before extraction: sha256sum -c SHA256SUMS
Extract into a clean working directory: unzip mt05_evidence.zip
Then: cd meridian_mt05 && sha256sum -c EVIDENCE_SHA256SUMS
Read case_context.txt and schema_guide.txt. Preserve original evidence and use
working copies, or open SQLite read-only with mode=ro.
'''+RULE

def manifest(folder,names):
    return ''.join(hashlib.sha256((folder/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names)

def build(root=ROOT):
    public=root/'public'; private=root/'private'
    public.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)/'meridian_mt05'; folder.mkdir()
        # Each row has a different exclusion reason; no source independently selects the answer.
        events=[
          ('ev-731','rst-418','08:12:00','export','failed',403,0,None),
          ('ev-732','rst-419','08:24:12','view','completed',200,0,None),
          ('ev-733','rst-420','07:59:59','export','completed',200,12,None),
          ('ev-734','pub-421','08:40:05','export','completed',200,-15,None),
          ('ev-735','rst-422','09:03:27','export','completed',200,20,'ev-735-retry'),
          ('ev-736','rst-423','09:14:39','export','completed',200,61,None),
          ('ev-737','rst-424','09:37:18','export','completed',200,-42,None),
          ('ev-738','rst-425','09:37:18','export','completed',500,8,None),
          ('ev-739','rst-426','09:52:01','export','cancelled',200,10,None),
          ('ev-740','rst-427','10:08:44','export','completed',200,15,'browser-other'),
          ('ev-741','rst-428','10:18:22','export','completed',200,25,'record-other'),
          ('ev-742','rst-429','11:00:00','export','completed',200,0,None),
          ('ev-743','rst-430','10:32:50','export','completed',200,0,'no-browser'),
        ]
        audit=[]; web=[]; visits=[]
        for i,(event,record,clock,action,status,http,delta,special) in enumerate(events):
            instant=datetime.fromisoformat('2026-10-17T'+clock+'+00:00')
            audit.append([event,record,'analyst-'+str(i%3+1),action,status,instant.astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(sep=' '),SOURCE])
            route=('/export/' if action=='export' else '/release/')+record
            wevent=special if special=='ev-735-retry' else event
            web.append(f'lab-session-{i%3+1} [{instant.strftime("%d/%b/%Y:%H:%M:%S %z")}] "GET {route} HTTP/1.1" {http} 384 event={wevent} record={record}')
            if special!='no-browser':
                bevent='ev-740-retry' if special=='browser-other' else event
                brecord='rst-499' if special=='record-other' else record
                visits.append((len(visits)+1,f'http://mt04.lab.invalid/{"export" if action=="export" else "release"}/{brecord}?event={bevent}','Meridian transfer workspace',int((instant+timedelta(seconds=delta)).timestamp())*1000,'export' if action=='export' else 'navigation'))
        for i in range(36):
            instant=datetime(2026,10,17,8,tzinfo=timezone.utc)+timedelta(seconds=i*277)
            event=f'nav-{800+i}'; record=f'pub-{600+i}'
            audit.append([event,record,'clerk-synthetic','view','completed',instant.astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(sep=' '),SOURCE])
            web.append(f'lab-background [{instant.strftime("%d/%b/%Y:%H:%M:%S %z")}] "GET /release/{record} HTTP/1.1" 200 256 event={event} record={record}')
            visits.append((len(visits)+1,f'http://mt04.lab.invalid/release/{record}?event={event}','Release register',int(instant.timestamp())*1000,'navigation'))
        # Stable source-order permutation prevents the target being an obvious end marker.
        audit.sort(key=lambda r:hashlib.sha256((SOURCE+r[0]).encode()).digest())
        web.sort(key=lambda r:hashlib.sha256((SOURCE+r).encode()).digest())
        with (folder/'application_audit.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f,lineterminator='\n'); writer.writerow(HEADERS); writer.writerows(audit)
        (folder/'web_access.log').write_text('\n'.join(web)+'\n',encoding='utf-8')
        with sqlite3.connect(folder/'browser_history.sqlite') as db:
            db.execute('PRAGMA page_size=4096')
            db.execute('CREATE TABLE visits (id INTEGER PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL, visit_time INTEGER NOT NULL, visit_type TEXT NOT NULL)')
            db.executemany('INSERT INTO visits VALUES (?,?,?,?,?)',visits); db.commit(); db.execute('VACUUM')
        (folder/'schema_guide.txt').write_text(GUIDE,encoding='utf-8')
        (folder/'case_context.txt').write_text(CONTEXT,encoding='utf-8')
        (folder/'EVIDENCE_SHA256SUMS').write_text(manifest(folder,FILES))
        result=solve(folder)
        selected=select(*load(folder))
        if len(selected)!=1: raise ValueError('Build requires one qualifying event')
        result['application_time']=selected[0]['application_time']
        result['audit_row']=selected[0]
        result['web_rows']=[line for line in web if 'event='+result['event_id']+' ' in line]
        result['browser_rows']=[v for v in visits if 'event='+result['event_id'] in v[1]]
        (private/'canonical_value.txt').write_bytes(result['canonical'].encode('utf-8'))
        (private/'flag.txt').write_text(result['flag']+'\n')
        (private/'expected_event.json').write_text(json.dumps(result,indent=2)+'\n')
        with zipfile.ZipFile(public/'mt05_evidence.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in sorted((*FILES,'EVIDENCE_SHA256SUMS')):
                info=zipfile.ZipInfo('meridian_mt05/'+name,(2026,10,17,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.create_system=3; info.external_attr=0o100644<<16
                z.writestr(info,(folder/name).read_bytes(),compresslevel=9)
    if (public/'mt05_evidence.zip').stat().st_size>=50*1024**2: raise ValueError('Archive too large')
    (public/'SHA256SUMS').write_text(manifest(public,['mt05_evidence.zip']))
    (public/'README.txt').write_text(README,encoding='utf-8')
    specification=(ROOT/'docs/MT05_SPECIFICATION.md').read_text(encoding='utf-8')
    (private/'solution.md').write_text(specification+'\n## Private author solution details\n\n'
        +'Verify outer and inner SHA-256 integrity before inventory and analysis. Parse CSV offsets, '
        +'query SQLite read-only and convert milliseconds to UTC, then correlate log identifiers, '
        +'completed status and the inclusive 60-second browser corroboration. Reject failed actions. '
        +'Serialize literal pipes, UTC uppercase Z and exact seconds without CR/LF, encode UTF-8, '
        +'SHA-256 and truncate to the first 16 lowercase hexadecimal characters.\n\n```json\n'
        +json.dumps(result,indent=2)+'\n```\n',encoding='utf-8')
    (private/'challenge_config.md').write_text('# MT-05 CTFd configuration\nStage: MT-05\nName: The Offset in the Handover Log\n'
        +'Category: Digital Forensics\nValue: 300\nDifficulty: Moderate-Hard\n'
        +'Type: standard/static\nState: visible\nFlag provider: static/exact\n'
        +'Prerequisite: none\nAttachments: mt05_evidence.zip, SHA256SUMS\n'
        +'Flag: '+result['flag']+'\n\n'+README+'\nHints (two free, cost 0 each):\n'
        +'1. The timestamp suffix or epoch definition determines the conversion. Normalize the relevant application event before correlating it.\n'
        +'2. Correlate identifiers and completion status first. Use browser history as corroboration, then build the canonical value exactly as specified.\n',encoding='utf-8')
    return result
if __name__=='__main__':
    build(); print('PASS: deterministic evidence generated; exactly one event; private answers written')
