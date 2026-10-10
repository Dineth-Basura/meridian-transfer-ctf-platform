"""Flask test-client checks for the single intended IDOR and its fixed decision."""
import hashlib
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app, export_allowed
from db import user_by_name, release_by_id, owned_releases
from seed import PARTICIPANT, OWN_IDS, TARGET_ID, flag, create_seed, training_password, verify_password

ROOT=Path('/app')
class MT04Unit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=create_app({'TESTING':True,'SECRET_KEY':'mt04-unit-test-only','SEED_DB_PATH':'/app/data/seed.sqlite'})
        cls.client=cls.app.test_client()
    def setUp(self):
        self.client.get('/logout')
        with self.client.session_transaction() as session: session.clear()
    def login(self,password=None,username=PARTICIPANT):
        page=self.client.get('/login').data.decode()
        token=re.search(r'name="csrf_token" value="([^"]+)"',page).group(1)
        return self.client.post('/login',data={'csrf_token':token,'username':username,'password':password or training_password(username)})
    def test_U01_seed_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/'a.sqlite',Path(d)/'b.sqlite'; create_seed(a); create_seed(b)
            self.assertEqual(hashlib.sha256(a.read_bytes()).digest(),hashlib.sha256(b.read_bytes()).digest())
    def test_U02_users(self):
        with self.app.app_context():
            self.assertTrue(all(user_by_name(u) for u in (PARTICIPANT,'archive_clerk','restricted_custodian')))
    def test_U03_hashed_passwords(self):
        with self.app.app_context():
            u=user_by_name(PARTICIPANT); self.assertNotEqual(u['password_hash'],training_password(PARTICIPANT)); self.assertTrue(verify_password(training_password(PARTICIPANT),u['password_hash']))
    def test_U04_participant_owns_records(self):
        with self.app.app_context():
            ids={r['id'] for r in owned_releases(user_by_name(PARTICIPANT)['id'])}; self.assertTrue(set(OWN_IDS)<=ids)
    def test_U05_target_other_owner(self):
        with self.app.app_context(): self.assertNotEqual(release_by_id(TARGET_ID)['owner_id'],user_by_name(PARTICIPANT)['id'])
    def test_U06_one_flag_in_target_data(self):
        with self.app.app_context():
            record=release_by_id(TARGET_ID); self.assertEqual(record['export_note'].count(flag()),1)
    def test_U07_flag_format(self): self.assertRegex(flag(),r'^MT\{mt04_[a-z0-9_]+\}$')
    def test_U08_guest_normal_denied(self): self.assertEqual(self.client.get(f'/release/{OWN_IDS[0]}').status_code,302)
    def test_U09_guest_export_denied(self): self.assertEqual(self.client.get(f'/export/{TARGET_ID}').status_code,302)
    def test_U10_own_normal_allowed(self): self.login(); self.assertEqual(self.client.get(f'/release/{OWN_IDS[0]}').status_code,200)
    def test_U11_own_export_allowed(self): self.login(); self.assertEqual(self.client.get(f'/export/{OWN_IDS[0]}').status_code,200)
    def test_U12_cross_normal_denied(self): self.login(); self.assertEqual(self.client.get(f'/release/{TARGET_ID}').status_code,404)
    def test_U13_cross_vulnerable_export_allowed(self): self.login(); self.assertEqual(self.client.get(f'/export/{TARGET_ID}').status_code,200)
    def test_U14_target_one_flag(self):
        self.login(); body=self.client.get(f'/export/{TARGET_ID}').data.decode(); self.assertEqual(len(re.findall(r'MT\{mt04_[a-z0-9_]+\}',body)),1)
    def test_U15_fixed_cross_denied(self):
        with self.app.app_context(): self.assertFalse(export_allowed(release_by_id(TARGET_ID),user_by_name(PARTICIPANT)['id'],enforce_owner=True))
    def test_U16_fixed_own_allowed(self):
        with self.app.app_context(): self.assertTrue(export_allowed(release_by_id(OWN_IDS[0]),user_by_name(PARTICIPANT)['id'],enforce_owner=True))
    def test_U17_static_no_flag(self):
        self.assertTrue(all(flag() not in p.read_text() for p in (ROOT/'static').rglob('*') if p.is_file()))
    def test_U18_templates_no_flag(self):
        self.assertTrue(all(flag() not in p.read_text() for p in (ROOT/'templates').rglob('*') if p.is_file()))
    def test_U19_login_errors_safe(self):
        response=self.login(password='definitely-wrong'); text=response.data.decode(); self.assertIn('Invalid training credentials',text); self.assertNotIn('pbkdf2_sha256',text); self.assertNotIn(training_password(PARTICIPANT),text)
    def test_U20_unknown_record_safe(self): self.login(); self.assertEqual(self.client.get('/export/999999').status_code,404)
    def test_U21_no_ctfd_admin_proxy(self):
        self.login()
        for path in ('/admin','/api/v1/users','/api/v1/configs'):
            response=self.client.get(path)
            self.assertEqual(response.status_code,404)
            self.assertNotIn('SECRET_KEY',response.data.decode())
    def test_U22_sql_like_id_rejected(self):
        self.login(); self.assertEqual(self.client.get('/export/1047%20OR%201=1').status_code,404)
    def test_U23_session_cookie_policy(self):
        cookie=self.login().headers.get('Set-Cookie','')
        self.assertIn('HttpOnly',cookie)
        self.assertIn('SameSite=Lax',cookie)
    def test_U24_login_csrf_required(self):
        self.client.get('/login')
        response=self.client.post('/login',data={'username':PARTICIPANT,'password':training_password(PARTICIPANT),'csrf_token':'invalid'})
        self.assertEqual(response.status_code,400)

if __name__=='__main__': unittest.main()
