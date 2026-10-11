#!/usr/bin/env python3
"""Signed-in downloads, public-only solvers, scoring and prior-stage preservation."""
import hashlib
import json
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from setup_mt01 import Client,ROOT,admin_client
from setup_mt05 import CHALLENGE,FILES

PRIOR={1:('Digital Footprints',100,'mt-01-digital-footprints'),2:('The Amended Contact Sheet',150,'mt-02-amended-contact-sheet'),3:('Dispatch Window',200,'mt-03-dispatch-window'),4:('Release Register Exception',250,'mt-04-release-register-exception')}

def snapshot(admin):
    details={}
    for i in PRIOR:
        d=admin.api(f'challenges/{i}')
        details[str(i)]={k:d.get(k) for k in ('name','category','value','state','type','description','requirements')}
        details[str(i)]['files']=admin.api(f'challenges/{i}/files')
    solves=[]; page=1
    while True:
        rows=admin.api(f'submissions?type=correct&page={page}')
        if not rows: break
        solves.extend(r['id'] for r in rows); page+=1
    return {'challenges':details,'solves':solves}

def test():
    admin=admin_client(); before=snapshot(admin)
    baseline=json.loads((ROOT/'.secrets/mt05_preflight_snapshot.json').read_text())
    assert before['challenges']==baseline['challenges']
    assert set(baseline['solves'])<=set(before['solves'])
    client=Client(); home,_=client.request('/'); assert b'Meridian Transfer' in home
    name='mt05_verify_'+secrets.token_hex(6)
    client.register_and_login({'name':name,'email':name+'@meridian.invalid','password':secrets.token_urlsafe(32)})
    user=client.api('users/me'); assert user['score']==0
    try:
        items=client.api('challenges')
        for cid,(title,value,folder) in PRIOR.items():
            found=[c for c in items if c['name']==title]; assert len(found)==1 and found[0]['value']==value
            d=client.api(f'challenges/{cid}'); assert d['state']=='visible'
            if cid<4:
                assert d['files']
                for url in d['files']:
                    filename=url.split('?')[0].rsplit('/',1)[1]
                    content,_=client.request(url)
                    assert content==(ROOT/'challenges'/folder/'public'/filename).read_bytes()
            else: assert 'http://127.0.0.1:8084' in d['description']
        found=[c for c in items if c['name']=='The Offset in the Handover Log']; assert len(found)==1
        cid=found[0]['id']; detail=client.api(f'challenges/{cid}')
        assert detail['state']=='visible' and detail['value']==300 and detail['type']=='standard' and not detail.get('requirements')
        assert len(detail['files'])==2
        with tempfile.TemporaryDirectory(prefix='mt05-participant-') as tmp:
            public=Path(tmp)
            for filename in FILES:
                url=next(u for u in detail['files'] if u.split('?')[0].endswith('/'+filename))
                content,_=client.request(url); assert content==(CHALLENGE/'public'/filename).read_bytes()
                (public/filename).write_bytes(content)
            (public/'README.txt').write_bytes((CHALLENGE/'public/README.txt').read_bytes())
            assert set(p.name for p in public.iterdir())=={'README.txt',*FILES}
            subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=public,check=True)
            # Scripts execute externally; clean dataset contains participant material only.
            answers=[]
            for script in ('reference_solver.py','independent_reference_solver.py'):
                output=subprocess.run([sys.executable,str(CHALLENGE/'author'/script),str(public),'--details'],capture_output=True,text=True,check=True)
                answers.append(json.loads(output.stdout))
            assert answers[0]==answers[1]
            flag=answers[0]['flag']; assert flag==(CHALLENGE/'private/flag.txt').read_text().strip()
        wrong=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt05_0000000000000000}'})
        assert wrong['status']=='incorrect' and client.api('users/me')['score']==0
        correct=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
        assert correct['status']=='correct' and client.api('users/me')['score']==300
        solves=client.api('users/me/solves'); assert len(solves)==1 and solves[0]['challenge_id']==cid
        duplicate=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
        assert duplicate['status']=='already_solved' and client.api('users/me')['score']==300 and len(client.api('users/me/solves'))==1
        after=snapshot(admin); assert before['challenges']==after['challenges']; assert set(before['solves'])<=set(after['solves'])
        result={k:'PASS' for k in ('CTFd HTTP','MT-05 visible and 300','No prerequisite','Participant downloads','Downloaded hashes','Public-only solver agreement','Wrong flag rejected','Correct flag accepted','Solve recorded','Duplicate scoring prevented','MT-01 regression','MT-02 regression','MT-03 regression','MT-04 configuration regression','Prior solves preserved')}
        result.update(timestamp=datetime.now(timezone.utc).isoformat(),challenge_id=cid,participant_id=user['id'])
        (ROOT/'.secrets/mt05_functional_result.json').write_text(json.dumps(result,indent=2)+'\n')
        for key,value in result.items():
            if value=='PASS': print('PASS:',key)
        return result
    finally: admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})
if __name__=='__main__': test()
