"""Live localhost HTTP behavior; no scanning or external target."""
import http.cookiejar
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8084'
class Hidden(HTMLParser):
    def __init__(self): super().__init__(); self.token=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='input' and a.get('name')=='csrf_token': self.token=a.get('value')
class LiveHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.creds=dict(line.split('=',1) for line in (ROOT/'private/credentials.txt').read_text().splitlines())
    def setUp(self):
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def get(self,path):
        with self.opener.open(BASE+path,timeout=8) as r: return r.status,r.read().decode(),r.geturl()
    def login(self,password=None):
        _,html,_=self.get('/login'); parser=Hidden(); parser.feed(html); self.assertTrue(parser.token)
        data=urllib.parse.urlencode({'username':self.creds['username'],'password':password or self.creds['password'],'csrf_token':parser.token}).encode()
        with self.opener.open(urllib.request.Request(BASE+'/login',data=data),timeout=8) as r: return r.status,r.read().decode(),r.geturl()
    def test_guest_login_page(self): self.assertIn('Release register sign in',self.get('/login')[1])
    def test_invalid_login(self): self.assertIn('Invalid training credentials',self.login('wrong')[1])
    def test_valid_login_and_list(self):
        _,html,url=self.login(); self.assertTrue(url.endswith('/releases')); self.assertIn('Related review reference: transfer record 1047',html)
    def test_own_record_and_export(self):
        self.login(); self.assertEqual(self.get('/release/1041')[0],200); self.assertEqual(self.get('/export/1041')[0],200)
    def test_cross_normal_denied(self):
        self.login()
        with self.assertRaises(urllib.error.HTTPError) as case: self.get('/release/1047')
        self.assertEqual(case.exception.code,404)
    def test_cross_vulnerable_export_one_flag(self):
        self.login(); code,body,_=self.get('/export/1047'); self.assertEqual(code,200); self.assertEqual(len(re.findall(r'MT\{mt04_[a-z0-9_]+\}',body)),1)
    def test_guest_target_export_denied(self): self.assertTrue(self.get('/export/1047')[2].endswith('/login'))
    def test_unknown_record_no_flag(self):
        self.login()
        with self.assertRaises(urllib.error.HTTPError) as case: self.get('/export/999999')
        self.assertEqual(case.exception.code,404)
        self.assertNotRegex(case.exception.read().decode(),r'MT\{mt04_[a-z0-9_]+\}')
    def test_logout_denies_afterwards(self):
        self.login(); _,html,_=self.get('/releases'); token=Hidden(); token.feed(html)
        data=urllib.parse.urlencode({'csrf_token':token.token}).encode()
        self.opener.open(urllib.request.Request(BASE+'/logout',data=data,method='POST'),timeout=8).read()
        self.assertTrue(self.get('/export/1047')[2].endswith('/login'))
if __name__=='__main__': unittest.main()
