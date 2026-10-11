#!/usr/bin/env python3
"""Real participant verification; preserves the solve and hides test account."""
import hashlib,json,secrets
from datetime import datetime,timezone
from setup_mt01 import Client,ROOT,admin_client
from setup_mt02 import CHALLENGE

def test():
    c=Client(); page,_=c.request('/'); assert b'Meridian Transfer' in page
    name='mt02_verify_'+secrets.token_hex(6)
    c.register_and_login({'name':name,'email':name+'@meridian.invalid','password':secrets.token_urlsafe(32)})
    user=c.api('users/me'); assert user['score']==0
    challenges=c.api('challenges')
    mt01=[x for x in challenges if x['name']=='Digital Footprints']; assert len(mt01)==1 and mt01[0]['value']==100
    mt02=[x for x in challenges if x['name']=='The Amended Contact Sheet']; assert len(mt02)==1 and mt02[0]['value']==150
    cid=mt02[0]['id']; detail=c.api(f'challenges/{cid}')
    assert detail['value']==150 and not detail.get('requirements')
    assert len(detail['files'])==2
    for filename in ('amended_contact_sheet.png','SHA256SUMS'):
        path=next(f for f in detail['files'] if f.split('?')[0].endswith('/'+filename))
        data,_=c.request(path)
        assert hashlib.sha256(data).digest()==hashlib.sha256((CHALLENGE/'public'/filename).read_bytes()).digest()
    wrong=c.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt02_definitely_wrong}'})
    assert wrong['status']=='incorrect' and c.api('users/me')['score']==0
    flag=(CHALLENGE/'private/flag.txt').read_text().strip()
    correct=c.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert correct['status']=='correct' and c.api('users/me')['score']==150
    solves=c.api('users/me/solves'); assert len(solves)==1 and solves[0]['challenge_id']==cid
    duplicate=c.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert duplicate['status']=='already_solved' and c.api('users/me')['score']==150 and len(c.api('users/me/solves'))==1
    admin=admin_client(); admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})
    result={'CTFd HTTP':'PASS','MT-01 regression':'PASS','MT-02 visible':'PASS','Participant download':'PASS','Wrong flag':'PASS','Correct flag':'PASS','Duplicate scoring':'PASS','No prerequisite':'PASS','challenge_id':cid,'participant_id':user['id'],'timestamp':datetime.now(timezone.utc).isoformat()}
    (ROOT/'.secrets/mt02_functional_result.json').write_text(json.dumps(result,indent=2)+'\n')
    for k,v in result.items(): print(f'{k}: {v}')
    return result
if __name__=='__main__': test()
