"""Contract tests, adversarial fixtures, independent agreement and recovery."""
import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'author'))
import reference_solver as main
import independent_reference_solver as second
from build_mt06 import build, context, event, encode
from validate_dataset import validate as dataset
from validate_public_release import validate as release

class MT06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.folder=main.unpack(ROOT/'public',Path(cls.tmp.name))
        cls.result=main.solve(ROOT/'public'); cls.other=second.solve(ROOT/'public')
        cls.raw=(cls.folder/'events.jsonl').read_bytes(); cls.bytes=bytes.fromhex(cls.result['serialized_hex'])
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def run_rows(self,rows):
        lines=encode(rows).decode().splitlines(); a=main.reconcile(lines,context()); b=second.reconcile(lines,context())
        self.assertEqual(a,b); return a
    def excluded(self,**kw): self.assertEqual(self.run_rows([event('toy-a',**kw)])['selected_count'],0)
    def included(self,**kw): self.assertEqual(self.run_rows([event('toy-a',**kw)])['selected_count'],1)
    def rejected(self,row): self.assertEqual(self.run_rows([row])['rejected_rows'],1)
    def test_MT06_T01(self): self.assertEqual(self.raw.count(b'\n'),1000); self.assertTrue(self.raw.endswith(b'\n'))
    def test_MT06_T02(self): self.assertTrue(all((self.folder/f).is_file() for f in (*main.FILES,'EVIDENCE_SHA256SUMS')))
    def test_MT06_T03(self): main.verify_manifest(ROOT/'public','SHA256SUMS',['mt06_ledger.zip'])
    def test_MT06_T04(self): main.verify_manifest(self.folder,'EVIDENCE_SHA256SUMS',main.FILES)
    def test_MT06_T05(self):
        with zipfile.ZipFile(ROOT/'public/mt06_ledger.zip') as z:
            self.assertTrue(all('..' not in PurePosixPath(n).parts and not PurePosixPath(n).is_absolute() and '\\' not in n for n in z.namelist()))
    def test_MT06_T06(self):
        with zipfile.ZipFile(ROOT/'public/mt06_ledger.zip') as z: self.assertEqual(set(z.namelist()),{'meridian_mt06/'+n for n in (*main.FILES,'EVIDENCE_SHA256SUMS')})
    def test_MT06_T07(self): self.assertEqual(json.loads((self.folder/'incident_context.json').read_text()),context())
    def test_MT06_T08(self): a,b=main.context_valid(context()); self.assertLess(a,b)
    def test_MT06_T09(self): self.assertEqual(len(context()['allowed_record_ids']),4)
    def test_MT06_T10(self): self.rejected('{broken')
    def test_MT06_T11(self): r=event('toy-a'); del r['status']; self.rejected(r)
    def test_MT06_T12(self):
        for key in main.FIELDS:
            for value in (None,42,True,[],{}): self.rejected(event('toy-a',**{key:value})) if key!='event_id' else self.rejected(dict(event('toy-a'),event_id=value))
    def test_MT06_T13(self): self.excluded(case_id='wrong-case')
    def test_MT06_T14(self): self.excluded(record_id='wrong-record')
    def test_MT06_T15(self): self.excluded(status='failed')
    def test_MT06_T16(self): self.excluded(status='pending')
    def test_MT06_T17(self): self.excluded(status='cancelled')
    def test_MT06_T18(self): self.excluded(seconds=-1)
    def test_MT06_T19(self): self.included(seconds=0)
    def test_MT06_T20(self): self.included(seconds=10799)
    def test_MT06_T21(self): self.excluded(seconds=10800)
    def test_MT06_T22(self): self.assertEqual(main.instant('2026-10-17T08:00:00Z').hour,8); self.included(offset=0)
    def test_MT06_T23(self): self.assertEqual(main.instant('2026-10-17T13:30:00+05:30').hour,8); self.included(offset=330)
    def test_MT06_T24(self): self.assertEqual(main.instant('2026-10-17T04:00:00-04:00').hour,8); self.included(offset=-240)
    def test_MT06_T25(self):
        for stamp,expected in [('2026-10-18T01:00:00+05:30','2026-10-17T19:30:00Z'),('2026-10-17T23:00:00-04:00','2026-10-18T03:00:00Z')]:
            self.assertEqual(main.instant(stamp).strftime('%Y-%m-%dT%H:%M:%SZ'),expected)
            self.assertEqual(second.Event.parse(json.dumps(event('toy-a',timestamp=stamp))).utc,main.instant(expected))
    def test_MT06_T26(self):
        for value in ('!','YQ=','YQ===','YR==','Y Q==','☃'): self.rejected(event('toy-a',token_b64=value))
    def test_MT06_T27(self): self.rejected(event('toy-a',token_b64='/w=='))
    def test_MT06_T28(self): r=event('toy-a'); out=self.run_rows([r,r]); self.assertEqual((out['selected_count'],out['retries']),(1,1))
    def test_MT06_T29(self):
        for change in ({'case_id':'other'},{'record_id':'other'},{'status':'failed'},{'timestamp':'2026-10-17T09:00:00Z'},{'token_b64':'eA=='}):
            for solver in (main,second):
                with self.assertRaisesRegex(ValueError,'Conflicting'): solver.reconcile(encode([event('toy-a'),event('toy-a',**change)]).decode().splitlines(),context())
    def test_MT06_T30(self):
        a,b=event('toy-a',10,'A'),event('toy-b',20,'B'); out=self.run_rows([b,a,b,a]); self.assertEqual(bytes.fromhex(out['serialized_hex']),b'A\nB')
    def test_MT06_T31(self):
        out=self.run_rows([event('toy-a',100,'Later',-240),event('toy-b',0,'Earlier',330)])
        self.assertEqual([r['event_id'] for r in out['selected']],['toy-b','toy-a'])
    def test_MT06_T32(self):
        out=self.run_rows([event('toy-z',100,'Z',0),event('toy-a',100,'A',330)])
        self.assertEqual([r['event_id'] for r in out['selected']],['toy-a','toy-z'])
    def test_MT06_T33(self): self.assertEqual(self.run_rows([event('toy-a',token='Decode me!')])['selected'][0]['token'],'Decode me!')
    def test_MT06_T34(self): self.assertEqual(self.run_rows([event('toy-a',token='  Case:Ä!?  ')])['selected'][0]['token'],'  Case:Ä!?  ')
    def test_MT06_T35(self): self.assertEqual(bytes.fromhex(self.run_rows([event('toy-a',token='A'),event('toy-b',token='B')])['serialized_hex']),b'A\nB')
    def test_MT06_T36(self): self.assertEqual(self.bytes.count(b'\n'),self.result['selected_count']-1); self.assertNotIn(b'\n\n',self.bytes)
    def test_MT06_T37(self): self.assertNotIn(b'\r',self.bytes)
    def test_MT06_T38(self): self.assertNotIn(b'\r\n',self.bytes)
    def test_MT06_T39(self): self.assertFalse(self.bytes.startswith(b'\n'))
    def test_MT06_T40(self): self.assertFalse(self.bytes.endswith(b'\n'))
    def test_MT06_T41(self): self.assertEqual(bytes.fromhex(self.run_rows([event('toy-a',token='café Δ')])['serialized_hex']),'café Δ'.encode('utf-8'))
    def test_MT06_T42(self): self.assertEqual(self.run_rows([event('toy-a',token='abc')])['sha256'],'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    def test_MT06_T43(self): self.assertRegex(self.result['sha256'],r'^[0-9a-f]{64}$')
    def test_MT06_T44(self): self.assertEqual(self.result['first32'],self.result['sha256'][:32]); self.assertEqual(len(self.result['first32']),32)
    def test_MT06_T45(self): self.assertRegex(self.result['flag'],r'^MT\{mt06_[0-9a-f]{32}\}$')
    def cli(self,name):
        p=subprocess.run([sys.executable,str(ROOT/'author'/name),'--details'],capture_output=True,text=True,check=True); return json.loads(p.stdout)
    def test_MT06_T46(self): self.assertEqual(self.cli('reference_solver.py'),self.result)
    def test_MT06_T47(self): self.assertEqual(self.cli('independent_reference_solver.py'),self.result)
    def test_MT06_T48(self): self.assertEqual([r['event_id'] for r in self.result['selected']],[r['event_id'] for r in self.other['selected']])
    def test_MT06_T49(self): self.assertEqual([r['token'] for r in self.result['selected']],[r['token'] for r in self.other['selected']])
    def test_MT06_T50(self): self.assertEqual(self.result['sha256'],self.other['sha256']); self.assertEqual(self.result['serialized_hex'],self.other['serialized_hex'])
    def test_MT06_T51(self): self.assertEqual(self.result['flag'],self.other['flag']); self.assertEqual(self.result,self.other)
    def test_MT06_T52(self):
        p=self.folder/'worked_example'; result=main.reconcile((p/'example_events.jsonl').read_text().splitlines(),json.loads((p/'example_context.json').read_text()))
        self.assertEqual(bytes.fromhex(result['serialized_hex']),b'Alpha\nBeta\nGamma'); self.assertIn(result['flag'],(p/'example_expected.txt').read_text())
    def test_MT06_T53(self): r=self.run_rows([]); self.assertEqual(r['selected_count'],0); self.assertEqual(r['sha256'],hashlib.sha256(b'').hexdigest())
    def test_MT06_T54(self): out=self.run_rows([event('toy-a',offset=0),event('toy-a',offset=330)]); self.assertEqual(out['retries'],1)
    def test_MT06_T55(self): self.test_MT06_T29()
    def test_MT06_T56(self): self.test_MT06_T25(); self.test_MT06_T31()
    def test_MT06_T57(self): self.test_MT06_T26()
    def test_MT06_T58(self): self.test_MT06_T32()
    def test_MT06_T59(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); a=build(root); first=(root/'public/mt06_ledger.zip').read_bytes(); b=build(root)
            self.assertEqual(a,b); self.assertEqual(first,(root/'public/mt06_ledger.zip').read_bytes()); self.assertEqual(first,(ROOT/'public/mt06_ledger.zip').read_bytes())
    def blobs(self): return [p.read_bytes() for p in (ROOT/'public').iterdir()]+[p.read_bytes() for p in self.folder.rglob('*') if p.is_file()]
    def test_MT06_T60(self): self.assertTrue(all(self.result['flag'].encode() not in b for b in self.blobs()))
    def test_MT06_T61(self):
        expected=(ROOT/'private/expected_selection.json').read_bytes(); self.assertTrue(all(expected not in b and self.bytes not in b for b in self.blobs()))
    def test_MT06_T62(self): self.assertTrue(release(ROOT/'public',verbose=False))
    def test_MT06_T63(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=main.unpack(ROOT/'public',Path(tmp)); (folder/'events.jsonl').write_bytes(b'corrupt\n')
            with self.assertRaises(ValueError): main.verify_manifest(folder,'EVIDENCE_SHA256SUMS',main.FILES)
    def test_MT06_T64(self):
        baseline=(ROOT/'public/mt06_ledger.zip').read_bytes()
        for _ in range(3):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); folder=main.unpack(ROOT/'public',root); (folder/'events.jsonl').write_bytes(b'corrupt\n')
                with self.assertRaises(ValueError): main.verify_manifest(folder,'EVIDENCE_SHA256SUMS',main.FILES)
                shutil.rmtree(folder); build(root/'rebuild')
                self.assertEqual((root/'rebuild/public/mt06_ledger.zip').read_bytes(),baseline)
                self.assertEqual(main.solve(root/'rebuild/public'),self.result)
    def test_MT06_T65_wrong_solution_variants(self):
        rows=[]
        for line in self.raw.decode().splitlines():
            try: r=json.loads(line); second.Event.parse(line); rows.append(r)
            except (ValueError,TypeError,UnicodeError): pass
        ctx=context(); start,end=main.context_valid(ctx)
        relevant=[r for r in rows if r['case_id']==ctx['case_id'] and r['record_id'] in ctx['allowed_record_ids'] and r['status']=='completed']
        qualifying=[r for r in relevant if start<=main.instant(r['timestamp'])<end]
        def unique(items): return list({r['event_id']:r for r in items}.values())
        def ordered(items): return sorted(items,key=lambda r:(main.instant(r['timestamp']),r['event_id']))
        def serialize(items,encoded=False): return '\n'.join(r['token_b64'] if encoded else base64.b64decode(r['token_b64']).decode('utf-8') for r in items).encode('utf-8')
        variants={
          'include exact end':serialize(ordered(unique([r for r in relevant if start<=main.instant(r['timestamp'])<=end]))),
          'exclude exact start':serialize(ordered(unique([r for r in relevant if start<main.instant(r['timestamp'])<end]))),
          'lexical timestamp':serialize(sorted(unique(qualifying),key=lambda r:(r['timestamp'],r['event_id']))),
          'ignore event tie':serialize(sorted(unique(qualifying),key=lambda r:main.instant(r['timestamp']))),
          'no dedup':serialize(ordered(qualifying)),
          'dedup after serialization':serialize(ordered(qualifying)),
          'Base64 text':serialize(ordered(unique(qualifying)),True),
          'CRLF':self.bytes.replace(b'\n',b'\r\n'),
          'trailing LF':self.bytes+b'\n',
        }
        for name,value in variants.items():
            with self.subTest(variant=name): self.assertNotEqual(hashlib.sha256(value).hexdigest()[:32],self.result['first32'])
        for wrong in (self.result['sha256'],self.result['first32'].upper(),self.result['sha256'][-32:]): self.assertNotEqual('MT{mt06_'+wrong+'}',self.result['flag'])
    def test_MT06_T66_invalid_timestamps(self):
        for value in ('2026-10-17T09:00:00','2026-02-30T09:00:00Z','2026-10-17T09:00:00+02:60','2026-10-17T09:00:00.5Z','2026-10-17T09:00:60Z'): self.rejected(event('toy-a',timestamp=value))
    def test_MT06_T67_invalid_identifiers_and_tokens(self):
        for value in ('ABC','évent','ev_1','x\n','1bad'): self.rejected(dict(event('toy-a'),event_id=value))
        for value in ('','a\nb','a\rb'): self.rejected(event('toy-a',token=value))
    def test_MT06_T68_private_exact_bytes(self):
        self.assertEqual((ROOT/'private/expected_serialization.bin').read_bytes(),self.bytes)
        self.assertEqual(dataset(ROOT/'public',ROOT/'private'),self.result)
    def test_MT06_T69_invalid_context(self):
        for change in ({'allowed_record_ids':[]},{'start_utc':context()['end_utc']},{'end_utc':'bad'}):
            for solver in (main,second):
                with self.assertRaises(ValueError): solver.reconcile([],dict(context(),**change))
    def test_MT06_T70_release_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'public'; shutil.copytree(ROOT/'public',p); (p/'answer.txt').write_text('not allowed')
            with self.assertRaises(ValueError): release(p,False)

if __name__=='__main__': unittest.main()
