#!/usr/bin/env python3
"""Real participant registration, download, submissions and score assertions."""
from pathlib import Path
import hashlib
import json
import secrets
from datetime import datetime, timezone
from setup_mt01 import Client, ROOT, CHALLENGE, BASE

def test():
    result = {}
    client = Client()
    page, _ = client.request('/')
    assert b'Meridian Transfer' in page
    result['CTFd HTTP'] = 'PASS'
    suffix = secrets.token_hex(6)
    username = 'mt01_verify_' + suffix
    client.register_and_login( {'name': username, 'email': username + '@meridian.invalid', 'password': secrets.token_urlsafe(32)})
    user = client.api('users/me')
    assert user['name'] == username and user['score'] == 0
    matches = [c for c in client.api('challenges') if c['name'] == 'Digital Footprints' and c['category'] == 'OSINT / Reconnaissance']
    assert len(matches) == 1
    cid = matches[0]['id']
    detail = client.api(f'challenges/{cid}')
    assert detail['value'] == 100 and detail['type'] == 'standard'
    result['Participant visibility'] = 'PASS'
    assert len(detail['files']) == 1
    path = detail['files'][0]
    assert path.split('?')[0].endswith('/digital_footprints.txt')
    downloaded, _ = client.request(path)
    baseline = (CHALLENGE / 'public/digital_footprints.txt').read_bytes()
    assert downloaded == baseline
    assert hashlib.sha256(downloaded).digest() == hashlib.sha256(baseline).digest()
    result['Attachment downloadable'] = 'PASS'
    wrong = client.api('challenges/attempt', 'POST', {'challenge_id': cid, 'submission': 'MT{mt01_definitely_wrong}'})
    assert wrong['status'] == 'incorrect'
    assert client.api('users/me')['score'] == 0
    result['Wrong flag rejected'] = 'PASS'
    flag = (CHALLENGE / 'private/flag.txt').read_text().strip()
    # Explicitly exercise case-sensitive matching as well.
    case = client.api('challenges/attempt', 'POST', {'challenge_id': cid, 'submission': flag.upper()})
    assert case['status'] == 'incorrect'
    result['Case sensitive flag'] = 'PASS'
    correct = client.api('challenges/attempt', 'POST', {'challenge_id': cid, 'submission': flag})
    assert correct['status'] == 'correct'
    assert client.api('users/me')['score'] == 100
    solves = client.api('users/me/solves')
    assert len(solves) == 1 and solves[0]['challenge_id'] == cid
    result['Correct flag accepted'] = 'PASS'
    result['Solve recorded'] = 'PASS'
    duplicate = client.api('challenges/attempt', 'POST', {'challenge_id': cid, 'submission': flag})
    assert duplicate['status'] == 'already_solved'
    assert client.api('users/me')['score'] == 100
    assert len(client.api('users/me/solves')) == 1
    assert client.api(f'challenges/{cid}')['value'] == 100
    result['Duplicate score prevented'] = 'PASS'
    result['challenge_id'] = cid
    result['participant_id'] = user['id']
    result['timestamp'] = datetime.now(timezone.utc).isoformat()
    # Preserve solves; hide the synthetic verification account from the public scoreboard.
    from setup_mt01 import admin_client
    admin = admin_client()
    assert admin.api('users/' + str(user['id']))['type'] == 'user'
    for account in admin.api('users'):
        if account['name'].startswith('mt01_verify_'):
            admin.api('users/' + str(account['id']), 'PATCH', {'hidden': True})
    (ROOT / '.secrets/mt01_functional_result.json').write_text(json.dumps(result, indent=2) + '\n')
    for key, value in result.items():
        if value == 'PASS':
            print('PASS: ' + key)
    print('PASS: functional participant ID ' + str(user['id']) + '; solve preserved; account hidden from scoreboard')
    return result

if __name__ == '__main__':
    test()
