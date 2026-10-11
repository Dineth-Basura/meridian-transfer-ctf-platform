#!/usr/bin/env python3
"""Real MT-03 participant checks; preserve solves and hide only test account."""
import hashlib
import json
import secrets
from datetime import datetime, timezone
from setup_mt01 import Client, ROOT, admin_client
from setup_mt03 import CHALLENGE, FILES

def test():
    client = Client()
    home,_ = client.request('/')
    assert b'Meridian Transfer' in home
    name = 'mt03_verify_' + secrets.token_hex(6)
    password = secrets.token_urlsafe(32)
    client.register_and_login( {'name':name,'email':name+'@meridian.invalid','password':password})
    user = client.api('users/me')
    assert user['name']==name and user['score']==0
    items = client.api('challenges')
    expected = {'Digital Footprints':100,'The Amended Contact Sheet':150,'Dispatch Window':200}
    for label,value in expected.items():
        matches=[c for c in items if c['name']==label]
        assert len(matches)==1 and matches[0]['value']==value
    cid=next(c['id'] for c in items if c['name']=='Dispatch Window')
    page,location=client.request('/challenges')
    assert location.endswith('/challenges') and b'Challenges' in page
    detail=client.api(f'challenges/{cid}')
    assert detail['state']=='visible' and detail['value']==200 and not detail.get('requirements')
    assert len(detail['files'])==3
    for filename in FILES:
        path=next(f for f in detail['files'] if f.split('?')[0].endswith('/'+filename))
        downloaded,_=client.request(path)
        baseline=(CHALLENGE/'public'/filename).read_bytes()
        assert hashlib.sha256(downloaded).digest()==hashlib.sha256(baseline).digest()
    wrong=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt03_definitely_wrong}'})
    assert wrong['status']=='incorrect' and client.api('users/me')['score']==0
    flag=(CHALLENGE/'private/flag.txt').read_text().strip()
    correct=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert correct['status']=='correct' and client.api('users/me')['score']==200
    solves=client.api('users/me/solves')
    assert len(solves)==1 and solves[0]['challenge_id']==cid
    duplicate=client.api('challenges/attempt','POST',{'challenge_id':cid,'submission':flag})
    assert duplicate['status']=='already_solved' and client.api('users/me')['score']==200
    assert len(client.api('users/me/solves'))==1
    admin=admin_client()
    admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'CTFd HTTP':'PASS','MT-01 visible and 100':'PASS','MT-02 visible and 150':'PASS','MT-03 visible and 200':'PASS','No prerequisite':'PASS','All attachments downloadable and hashes match':'PASS','Wrong flag':'PASS','Correct flag':'PASS','Solve recorded':'PASS','Duplicate scoring':'PASS','challenge_id':cid,'participant_id':user['id']}
    (ROOT/'.secrets/mt03_functional_result.json').write_text(json.dumps(result,indent=2)+'\n')
    for key,value in result.items():
        if value=='PASS': print('PASS:',key)
    return result

if __name__=='__main__':
    test()
