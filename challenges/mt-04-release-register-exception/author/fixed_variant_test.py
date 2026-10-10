#!/usr/bin/env python3
"""Private fixed authorization comparison; no participant route added."""
from app import create_app, export_allowed
from db import release_by_id, user_by_name
from seed import PARTICIPANT, OWN_IDS, TARGET_ID

def test():
    app=create_app({'TESTING':True,'SECRET_KEY':'mt04-fixed-test-only'})
    with app.app_context():
        uid=user_by_name(PARTICIPANT)['id']
        assert export_allowed(release_by_id(OWN_IDS[0]),uid,enforce_owner=True)
        assert not export_allowed(release_by_id(TARGET_ID),uid,enforce_owner=True)
        assert export_allowed(release_by_id(TARGET_ID),uid,enforce_owner=False)
    print('PASS: fixed owner export allowed; fixed cross-owner denied; vulnerable cross-owner allowed')
if __name__=='__main__': test()
