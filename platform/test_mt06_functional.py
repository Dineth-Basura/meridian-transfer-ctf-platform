#!/usr/bin/env python3
"""AUTOMATED TECHNICAL E2E, six stages; never claims human acceptance."""
import argparse
import hashlib
import json
import secrets
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime,timezone
from pathlib import Path
from setup_mt01 import Client,ROOT,admin_client

STAGES=[('Digital Footprints',100,'mt-01-digital-footprints'),('The Amended Contact Sheet',150,'mt-02-amended-contact-sheet'),('Dispatch Window',200,'mt-03-dispatch-window'),('Release Register Exception',250,'mt-04-release-register-exception'),('The Offset in the Handover Log',300,'mt-05-offset-handover-log'),('Reconcile the Transfer Ledger',400,'mt-06-reconcile-transfer-ledger')]
SNAPSHOT=ROOT/'.secrets/mt06_preflight_snapshot.json'

def snapshot(admin):
    details={}
    for title,value,folder in STAGES[:5]:
        found=[x for x in admin.api('challenges') if x['name']==title]; assert len(found)==1
        cid=found[0]['id']; d=admin.api(f'challenges/{cid}')
        details[str(cid)]={k:d.get(k) for k in ('name','category','description','value','state','type','requirements')}
        for suffix in ('files','flags','hints'): details[str(cid)][suffix]=admin.api(f'challenges/{cid}/{suffix}')
    solves=[]; page=1
    while True:
        rows=admin.api(f'submissions?type=correct&page={page}')
        if not rows: break
        solves.extend(r['id'] for r in rows); page+=1
    return dict(challenges=details,solves=solves)

def check_preserved(before,after):
    assert before['challenges']==after['challenges'], 'Prior challenge configuration changed'
    assert set(before['solves'])<=set(after['solves']), 'Prior correct submissions lost'

def derive(stage,folder,public):
    author=ROOT/'challenges'/folder/'author'
    code={1:"from reference_solver import solve; print('MT{mt01_'+solve(p/'digital_footprints.txt')+'}')",2:"from reference_extractor import extract; print(extract(p/'amended_contact_sheet.png')[2])",3:"from reference_solver import solve; print(solve(p)[1])",4:"from reference_poc import solve; print(solve())"}
    if stage<5:
        script='import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); p=Path(sys.argv[2]); '+code[stage]
        result=subprocess.run([str(ROOT/'.venv-author/bin/python'),'-c',script,str(author),str(public)],capture_output=True,text=True,check=True)
        return result.stdout.strip().splitlines()[-1]
    results=[]
    for name in ('reference_solver.py','independent_reference_solver.py'):
        proc=subprocess.run([sys.executable,str(author/name),str(public),'--details'],capture_output=True,text=True,check=True)
        results.append(json.loads(proc.stdout))
    assert results[0]==results[1], 'Independent intermediate mismatch'
    return results[0]['flag']

def test():
    admin=admin_client(); before=snapshot(admin)
    check_preserved(json.loads(SNAPSHOT.read_text()),before)
    client=Client(); home,_=client.request('/'); assert b'Meridian Transfer' in home
    username='mt06_e2e_'+secrets.token_hex(6)
    client.register_and_login(dict(name=username,email=username+'@meridian.invalid',password=secrets.token_urlsafe(32)))
    user=client.api('users/me'); assert user['score']==0
    results={'timestamp':datetime.now(timezone.utc).isoformat(),'CTFd HTTP':'PASS'}
    try:
        items=client.api('challenges'); total=0; stage_results={}
        for index,(title,value,folder) in enumerate(STAGES,1):
            found=[c for c in items if c['name']==title]; assert len(found)==1 and found[0]['value']==value
            cid=found[0]['id']; detail=client.api(f'challenges/{cid}')
            assert detail['state']=='visible' and detail['type']=='standard' and not detail.get('requirements')
            with tempfile.TemporaryDirectory(prefix=f'mt{index:02}-download-') as tmp:
                public=Path(tmp)
                for url in detail['files']:
                    name=url.split('?')[0].rsplit('/',1)[1]
                    data,_=client.request(url)
                    assert data==(ROOT/'challenges'/folder/'public'/name).read_bytes()
                    (public/name).write_bytes(data)
                if index!=4:
                    if index==1 and not (public/'SHA256SUMS').exists():
                        # MT-01's established CTFd contract uploads only the evidence file.
                        manifest=(ROOT/'challenges'/folder/'public/SHA256SUMS').read_text()
                        assert manifest==hashlib.sha256((public/'digital_footprints.txt').read_bytes()).hexdigest()+'  digital_footprints.txt\n'
                    else:
                        assert (public/'SHA256SUMS').is_file()
                        subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=public,check=True,capture_output=True)
                    (public/'README.txt').write_bytes((ROOT/'challenges'/folder/'public/README.txt').read_bytes())
                if index==6:
                    assert {p.name for p in public.iterdir()}=={'README.txt','mt06_ledger.zip','SHA256SUMS'}
                    with zipfile.ZipFile(public/'mt06_ledger.zip') as z: z.extractall(public/'working')
                    subprocess.run(['sha256sum','-c','EVIDENCE_SHA256SUMS'],cwd=public/'working/meridian_mt06',check=True,capture_output=True)
                flag=derive(index,folder,public)
                assert flag==(ROOT/'challenges'/folder/'private/flag.txt').read_text().strip()
            def attempt(submission):
                time.sleep(7)  # Stay below the installed 10-attempt/minute protection.
                return client.api('challenges/attempt','POST',dict(challenge_id=cid,submission=submission))
            for wrong in ('MT{mt%02d_%s}' % (index,'0'*32),'malformed-wrong'):
                assert attempt(wrong)['status']=='incorrect'
                assert client.api('users/me')['score']==total
            assert attempt(flag)['status']=='correct'
            total+=value; assert client.api('users/me')['score']==total
            assert attempt(flag)['status']=='already_solved'
            assert client.api('users/me')['score']==total
            assert len([s for s in client.api('users/me/solves') if s['challenge_id']==cid])==1
            stage_results[f'MT-{index:02}']={k:'PASS' for k in ('visibility/value','attachments/service','reference path','wrong flag','malformed flag','correct flag','single scoring award')}
            print(f'PASS: MT-{index:02} downloads/reference path, wrong/correct flags, single scoring award',flush=True)
        assert total == sum(s[1] for s in STAGES) == 1400, f'Unexpected total score: {total}'
        assert len(client.api('users/me/solves'))==6
        # Rebuild only assets three times; CTFd solve IDs must remain exactly unchanged.
        recovery_before=snapshot(admin); challenge=ROOT/'challenges/mt-06-reconcile-transfer-ledger'
        baseline=(challenge/'public/mt06_ledger.zip').read_bytes()
        for _ in range(3):
            subprocess.run([sys.executable,str(challenge/'author/build_mt06.py')],check=True,capture_output=True)
            assert (challenge/'public/mt06_ledger.zip').read_bytes()==baseline
            assert derive(6,'mt-06-reconcile-transfer-ledger',challenge/'public')==flag
        assert snapshot(admin)==recovery_before
        check_preserved(before,snapshot(admin))
        results.update(stages=stage_results,total_points=total,recovery_cycles=3,prior_configuration_preserved='PASS',prior_solves_preserved='PASS',recovery_solves_unchanged='PASS',automated_technical_e2e='PASS',participant_id=user['id'])
        (ROOT/'.secrets/mt06_functional_result.json').write_text(json.dumps(results,indent=2)+'\n')
        print('PASS: 1400 total, recovery x3, prior configuration and all existing solves preserved')
        return results
    finally: admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--snapshot',action='store_true'); a=p.parse_args()
    if a.snapshot:
        if SNAPSHOT.exists(): raise SystemExit('Refusing to overwrite original snapshot')
        SNAPSHOT.write_text(json.dumps(snapshot(admin_client()),indent=2)+'\n'); SNAPSHOT.chmod(0o600); print('PASS: original five-stage configuration and solve snapshot saved privately')
    else: test()
