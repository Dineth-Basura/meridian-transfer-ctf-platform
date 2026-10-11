#!/usr/bin/env python3
"""Real CTFd MT-04 participant and score test; preserve hidden test solve."""
import json
import secrets
from datetime import datetime,timezone
from setup_mt01 import Client, ROOT, admin_client
from setup_mt04 import CHALLENGE

def test():
    client=Client(); page,_=client.request('/')
    assert b'Meridian Transfer' in page
    name='mt04_verify_'+secrets.token_hex(6)
    client.register_and_login({'name':name,'email':name+'@meridian.invalid','password':secrets.token_urlsafe(32)})
    user=client.api('users/me'); assert user['score']==0
    expected={'Digital Footprints':100,'The Amended Contact Sheet':150,'Dispatch Window':200,'Release Register Exception':250}
    items=client.api('challenges')
    for title,value in expected.items():
        matches=[c for c in items if c['name']==title]
        assert len(matches)==1 and matches[0]['value']==value
    cid=next(c['id'] for c in items if c['name']=='Release Register Exception')
    detail=client.api(f'challenges/{cid}')
    assert detail['state']=='visible' and detail['type']=='standard' and detail['value']==250 and not detail.get('requirements')
    assert 'http://127.0.0.1:8084' in detail['description']
    wrong=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt04_definitely_wrong}'})
    assert wrong['status']=='incorrect' and client.api('users/me')['score']==0
    flag=(CHALLENGE/'private/flag.txt').read_text().strip()
    correct=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert correct['status']=='correct' and client.api('users/me')['score']==250
    solves=client.api('users/me/solves'); assert len(solves)==1 and solves[0]['challenge_id']==cid
    duplicate=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert duplicate['status']=='already_solved' and client.api('users/me')['score']==250
    admin=admin_client(); admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'CTFd HTTP':'PASS','prior stages visible and valued':'PASS','MT-04 visible and 250':'PASS','no prerequisite':'PASS','wrong flag rejected':'PASS','correct flag accepted':'PASS','solve recorded':'PASS','duplicate scoring prevented':'PASS','challenge_id':cid,'participant_id':user['id']}
    (ROOT/'.secrets/mt04_functional_result.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,value in result.items():
        if value=='PASS': print('PASS:',name)
    return result
if __name__=='__main__': test()
