"""Forty contract checks, including adversarial selection and restore fixtures."""
import copy
import csv
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'author'))
import reference_solver as main
import independent_reference_solver as second
from build_mt05 import build, manifest
from validate_public_release import validate

class MT05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.folder=main.unpack(ROOT/'public',Path(cls.tmp.name))
        cls.data=main.load(cls.folder); cls.result=main.solve(cls.folder)
        cls.expected=json.loads((ROOT/'private/expected_event.json').read_text())
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def fixture(self):
        context,audit,web,visits=copy.deepcopy(self.data)
        target=next(r for r in audit if r['event_id']==self.result['event_id'])
        audit=[target]
        return context,audit,web,visits
    def test_MT05_T01(self): self.assertTrue(all((ROOT/'public'/n).is_file() for n in ('mt05_evidence.zip','SHA256SUMS','README.txt')))
    def test_MT05_T02(self): self.assertLess((ROOT/'public/mt05_evidence.zip').stat().st_size,50*1024**2)
    def test_MT05_T03(self):
        with zipfile.ZipFile(ROOT/'public/mt05_evidence.zip') as z:
            self.assertEqual(set(z.namelist()),{'meridian_mt05/'+n for n in (*main.FILES,'EVIDENCE_SHA256SUMS')}); self.assertEqual(len(z.infolist()),6)
    def test_MT05_T04(self): main.verify_manifest(ROOT/'public','SHA256SUMS',['mt05_evidence.zip'])
    def test_MT05_T05(self): main.verify_manifest(self.folder,'EVIDENCE_SHA256SUMS',main.FILES)
    def test_MT05_T06(self):
        with (self.folder/'application_audit.csv').open() as f: self.assertEqual(next(csv.reader(f)),main.HEADERS)
    def test_MT05_T07(self): self.assertEqual(len(self.data[2]),len((self.folder/'web_access.log').read_text().splitlines()))
    def test_MT05_T08(self):
        with sqlite3.connect((self.folder/'browser_history.sqlite').as_uri()+'?mode=ro',uri=True) as db:
            with self.assertRaises(sqlite3.OperationalError): db.execute('CREATE TABLE forbidden(x)')
    def test_MT05_T09(self):
        with sqlite3.connect((self.folder/'browser_history.sqlite').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual([(r[1],r[2]) for r in db.execute('PRAGMA table_info(visits)')],[('id','INTEGER'),('url','TEXT'),('title','TEXT'),('visit_time','INTEGER'),('visit_type','TEXT')])
    def test_MT05_T10(self): self.assertEqual(main.application_time('2026-10-17 14:30:00+05:30').hour,9)
    def test_MT05_T11(self):
        self.assertEqual(main.application_time('2026-10-17 04:00:00-05:00'),datetime(2026,10,17,9,tzinfo=timezone.utc))
        self.assertEqual(self.result['utc_timestamp'],self.expected['utc_timestamp'])
    def test_MT05_T12(self):
        for original,utc in [('2026-01-01 00:15:00+05:30','2025-12-31T18:45:00Z'),('2026-10-31 23:30:00-02:00','2026-11-01T01:30:00Z')]:
            self.assertEqual(main.application_time(original).strftime('%Y-%m-%dT%H:%M:%SZ'),utc)
    def test_MT05_T13(self):
        c,a,w,v=self.fixture(); t=self.result['utc_timestamp']; c['window_end']=t; self.assertEqual(main.select(c,a,w,v),[])
        c['window_start']=t; c['window_end']='2026-10-17T11:00:00Z'; self.assertEqual(len(main.select(c,a,w,v)),1)
    def test_MT05_T14(self):
        for status in ('failed','cancelled'):
            c,a,w,v=self.fixture(); a[0]['status']=status; self.assertEqual(main.select(c,a,w,v),[])
    def test_MT05_T15(self):
        c,a,w,v=self.fixture(); a[0]['action']='view'; self.assertEqual(main.select(c,a,w,v),[])
    def test_MT05_T16(self):
        c,a,w,v=self.fixture(); c['restricted_prefix']='unrelated-'; self.assertEqual(main.select(c,a,w,v),[])
    def browser_delta(self,delta):
        c,a,w,v=self.fixture(); t=main.application_time(a[0]['application_time']); event=a[0]['event_id']
        v=[(i,u,title,int(t.timestamp()*1000)+delta,kind) for i,u,title,ms,kind in v if 'event='+event in u]
        return main.select(c,a,w,v)
    def test_MT05_T17(self):
        for delta in (-60000,0,60000): self.assertEqual(len(self.browser_delta(delta)),1)
    def test_MT05_T18(self):
        for delta in (-60001,60001): self.assertEqual(self.browser_delta(delta),[])
    def test_MT05_T19(self):
        for source,field in [('web','event'),('web','record'),('web','status')]:
            c,a,w,v=self.fixture()
            for row in w:
                if row['event']==a[0]['event_id']: row[field]='403' if field=='status' else 'other'
            self.assertEqual(main.select(c,a,w,v),[])
        c,a,w,v=self.fixture(); self.assertEqual(main.select(c,a,w,[]),[])
        v=[(i,u.replace(a[0]['event_id'],'ev-other'),t,ms,k) for i,u,t,ms,k in v]; self.assertEqual(main.select(c,a,w,v),[])
    def test_MT05_T20(self):
        self.assertEqual(len(main.select(*self.data)),1)
        c,a,w,v=self.fixture(); a[0]['status']='failed'; self.assertEqual(main.select(c,a,w,v),[])
        # A second fully corroborated event really is counted, preventing a first-match shortcut.
        c,a,w,v=self.fixture(); clone=dict(a[0],event_id='ev-additional'); a.append(clone)
        matching=next(r for r in w if r['event']==a[0]['event_id']); w.append(dict(matching,event='ev-additional'))
        visit=next(r for r in v if 'event='+a[0]['event_id'] in r[1]); v.append((999,visit[1].replace(a[0]['event_id'],'ev-additional'),*visit[2:]))
        self.assertEqual(len(main.select(c,a,w,v)),2)
    def test_MT05_T21(self):
        for bad in ('EV-a','évent',' event','event\n','ev|x'):
            with self.assertRaises(ValueError): main.canonical(bad,datetime.now(timezone.utc).replace(microsecond=0),'rst-a')
            with self.assertRaises(ValueError): second.serialize(bad,'2026-10-17T09:00:00Z','rst-a')
    def test_MT05_T22(self):
        for bad in ('RST-a','réc','rst a','rst\r\n'):
            with self.assertRaises(ValueError): main.canonical('ev-a',datetime(2026,1,1,tzinfo=timezone.utc),bad)
            with self.assertRaises(ValueError): second.serialize('ev-a','2026-10-17T09:00:00Z',bad)
    def test_MT05_T23(self):
        self.assertRegex(self.result['utc_timestamp'],r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
        for t in (datetime(2026,1,1),datetime(2026,1,1,tzinfo=timezone(timedelta(hours=1))),datetime(2026,1,1,microsecond=1,tzinfo=timezone.utc)):
            with self.assertRaises(ValueError): main.canonical('ev-a',t,'rst-a')
        for t in ('2026-10-17T09:00:00z','2026-10-17T09:00:00.000Z','2026-10-17T09:00:00+00:00'):
            with self.assertRaises(ValueError): second.serialize('ev-a',t,'rst-a')
    def test_MT05_T24(self): self.assertEqual(self.result['canonical'].split('|'),[self.result[k] for k in ('event_id','utc_timestamp','record_id')])
    def test_MT05_T25(self): self.assertFalse(any(c.isspace() for c in self.result['canonical']))
    def test_MT05_T26(self): self.assertEqual((ROOT/'private/canonical_value.txt').read_bytes(),self.result['canonical'].encode())
    def test_MT05_T27(self): self.assertEqual(bytes.fromhex(self.result['canonical_utf8_hex']),self.result['canonical'].encode('utf-8'))
    def test_MT05_T28(self): self.assertRegex(self.result['sha256'],r'^[0-9a-f]{64}$')
    def test_MT05_T29(self): self.assertEqual(self.result['first16'],hashlib.sha256(self.result['canonical'].encode('utf-8')).hexdigest()[:16])
    def test_MT05_T30(self): self.assertRegex(self.result['flag'],r'^MT\{mt05_[0-9a-f]{16}\}$')
    def run_solver(self,name):
        result=subprocess.run([sys.executable,str(ROOT/'author'/name),'--details'],capture_output=True,text=True,check=True)
        return json.loads(result.stdout)
    def test_MT05_T31(self): self.assertEqual(self.run_solver('reference_solver.py'),{k:self.expected[k] for k in self.result})
    def test_MT05_T32(self): self.assertEqual(self.run_solver('independent_reference_solver.py'),{k:self.expected[k] for k in self.result})
    def test_MT05_T33(self):
        other=second.solve(ROOT/'public')
        for k in ('event_id','utc_timestamp','record_id','canonical','canonical_utf8_hex','sha256','first16'): self.assertEqual(self.result[k],other[k],k)
    def test_MT05_T34(self): self.assertEqual(self.result['flag'],second.solve(ROOT/'public')['flag'])
    def public_blobs(self): return [p.read_bytes() for p in (ROOT/'public').iterdir()]+[p.read_bytes() for p in self.folder.iterdir()]
    def test_MT05_T35(self): self.assertTrue(all(self.result['flag'].encode() not in b for b in self.public_blobs()))
    def test_MT05_T36(self): self.assertTrue(all(self.result['canonical'].encode() not in b for b in self.public_blobs()))
    def test_MT05_T37(self): self.assertTrue(validate(ROOT/'public',verbose=False))
    def test_MT05_T38(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp); build(target); one=(target/'public/mt05_evidence.zip').read_bytes(); build(target)
            self.assertEqual(one,(target/'public/mt05_evidence.zip').read_bytes()); self.assertEqual(one,(ROOT/'public/mt05_evidence.zip').read_bytes())
    def test_MT05_T39(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=main.unpack(ROOT/'public',Path(tmp)); (folder/'web_access.log').write_text('tampered\n')
            with self.assertRaises(ValueError): main.solve(folder)
    def test_MT05_T40(self):
        baseline=(ROOT/'public/mt05_evidence.zip').read_bytes()
        for _ in range(3):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); working=main.unpack(ROOT/'public',root)
                (working/'application_audit.csv').write_bytes(b'corrupt')
                with self.assertRaises(ValueError): main.verify_manifest(working,'EVIDENCE_SHA256SUMS',main.FILES)
                shutil.rmtree(working); build(root/'rebuild')
                self.assertEqual(baseline,(root/'rebuild/public/mt05_evidence.zip').read_bytes())
                restored=main.unpack(root/'rebuild/public',root/'restored'); self.assertEqual(main.solve(restored),self.result)
                self.assertEqual(baseline,(ROOT/'public/mt05_evidence.zip').read_bytes())

if __name__=='__main__': unittest.main()
