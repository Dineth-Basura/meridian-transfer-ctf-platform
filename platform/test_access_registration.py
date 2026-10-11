#!/usr/bin/env python3
"""Regression checks of real session boundaries; no database manipulation."""
import json
import secrets
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlparse
from setup_mt01 import Client, admin_client, ROOT

def blocked(client):
    for path in ('/admin', '/admin/users', '/admin/challenges'):
        _, location = client.request(path)
        assert urlparse(location).path == '/login', path + ' leaked an admin page'
    for path in ('/api/v1/flags', '/api/v1/configs'):
        try:
            client.request(path, content_type='application/json')
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError(path + ' allowed protected API access')

def test():
    guest = Client()
    blocked(guest)
    body, _ = guest.request('/')
    assert b'Admin Panel' not in body and b'Create participant account' in body
    body, location = guest.request('/register')
    assert urlparse(location).path == '/register' and b'name="password"' in body
    suffix = secrets.token_hex(6)
    name = 'mt01_verify_access_' + suffix
    password = secrets.token_urlsafe(32)
    _, location = guest.form('/register?next=/challenges', {'name': name, 'email': name+'@meridian.invalid', 'password': password, 'type': 'admin'})
    assert urlparse(location).path == '/login'
    _, location = guest.request('/challenges')
    assert urlparse(location).path == '/login'
    body, location = guest.form('/login', {'name': name, 'password': 'incorrect-password'})
    assert urlparse(location).path == '/login' and b'incorrect' in body
    _, location = guest.form('/login?next=/settings', {'name': name, 'password': password})
    assert urlparse(location).path == '/challenges'
    user = guest.api('users/me')
    assert user['name'] == name
    blocked(guest)
    body, _ = guest.request('/')
    assert b'Admin Panel' not in body and b'Participant' in body and b'Sign out' in body
    # Role escalation through the participant user-edit API must be ignored/rejected.
    try:
        guest.api('users/me', 'PATCH', {'type': 'admin'})
    except (HTTPError, RuntimeError):
        pass
    blocked(guest)
    admin = admin_client()
    assert admin.api('users/'+str(user['id']))['type'] == 'user'
    body, location = admin.request('/admin')
    assert urlparse(location).path.startswith('/admin')
    home, _ = admin.request('/')
    assert b'Administrator' in home and b'Sign out' in home
    # Sign out, register page, then log back in with participant credentials.
    guest.request('/logout')
    blocked(guest)
    body, location = guest.request('/register')
    assert urlparse(location).path == '/register' and b'name="password"' in body
    guest.form('/login', {'name': name, 'password': password})
    assert guest.api('users/me')['name'] == name
    blocked(guest)
    assert admin.api('users/'+str(user['id']))['type'] == 'user'
    admin.api('users/'+str(user['id']), 'PATCH', {'hidden': True})
    result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'Anonymous admin access blocked': 'PASS',
              'Participant admin access blocked': 'PASS', 'Registration and participant login': 'PASS',
              'Role escalation blocked': 'PASS', 'Administrator login': 'PASS', 'Logout restores registration': 'PASS'}
    (ROOT / 'ACCESS_REGISTRATION_STATUS.json').write_text(json.dumps(result, indent=2)+'\n')
    for key, value in result.items():
        if value == 'PASS': print('PASS: '+key)

if __name__ == '__main__':
    test()
