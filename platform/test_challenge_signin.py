#!/usr/bin/env python3
"""Verify guest challenge denial and signed-in participant access."""
from urllib.error import HTTPError
from urllib.parse import urlparse
import secrets
from setup_mt01 import Client, admin_client, ROOT

def check():
    admin=admin_client()
    challenges=admin.api('challenges')
    assert {c['name'] for c in challenges}>={'Digital Footprints','The Amended Contact Sheet'}
    cid=next(c['id'] for c in challenges if c['name']=='The Amended Contact Sheet')
    attachment=admin.api(f'challenges/{cid}')['files'][0]
    guest=Client()
    home,_=guest.request('/'); assert b'Create participant account' in home and b'Sign in to play' in home
    page,url=guest.request('/challenges'); assert urlparse(url).path=='/login'
    try: guest.request('/api/v1/challenges',content_type='application/json')
    except HTTPError as e: assert e.code==403
    else: raise AssertionError('Guest challenge API accessible')
    try: guest.request(attachment)
    except HTTPError as e: assert e.code==403
    else: raise AssertionError('Guest attachment accessible')
    guest.refresh_nonce()
    try: guest.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt02_definitely_wrong}'})
    except HTTPError as e: assert e.code in (401,403)
    else: raise AssertionError('Guest submission accepted')
    name='signin_verify_'+secrets.token_hex(6)
    guest.register_and_login({'name':name,'email':name+'@meridian.invalid','password':secrets.token_urlsafe(32)})
    user=guest.api('users/me'); assert user['name']==name
    page,url=guest.request('/challenges'); assert urlparse(url).path=='/challenges' and b'Challenges' in page
    visible=guest.api('challenges'); assert {c['name'] for c in visible}>={'Digital Footprints','The Amended Contact Sheet'}
    data,_=guest.request(attachment); assert len(data)>0
    wrong=guest.api('challenges/attempt','POST',{'challenge_id':cid,'submission':'MT{mt02_definitely_wrong}'})
    assert wrong['status']=='incorrect'
    guest.request('/logout')
    _,after_logout=guest.request('/challenges'); assert urlparse(after_logout).path=='/login'
    admin.api(f'users/{user["id"]}','PATCH',{'hidden':True})
    print('PASS: guest homepage and registration available')
    print('PASS: guest challenge page redirects to sign-in')
    print('PASS: guest challenge API, attachment and submission denied')
    print('PASS: signed-in participant can view stages, download, and submit')
    print('PASS: logout restores challenge denial')
if __name__=='__main__': check()
