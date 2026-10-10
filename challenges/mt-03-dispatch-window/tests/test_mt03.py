"""MT-03 contract tests, including negative and public-only checks."""
import base64
import binascii
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'public'
sys.path.insert(0, str(ROOT/'author'))
from build_mt03 import build, caesar_ascii, plaintext, FLAG, RELEASE_DATE
from reference_solver import solve, parse_release_key, decode_ciphertext, reverse_ascii_shift

class MT03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.flag = (ROOT/'private/flag.txt').read_text().strip()
        cls.notice = (PUBLIC/'release_notice.txt').read_text()
        cls.raw = (PUBLIC/'dispatch_ciphertext.txt').read_bytes()
        cls.key = parse_release_key(cls.notice)[1]

    def test_T01_files(self):
        self.assertEqual({p.name for p in PUBLIC.iterdir()}, {'dispatch_ciphertext.txt','release_notice.txt','SHA256SUMS','README.txt'})
    def test_T02_deterministic(self):
        first={p.name:p.read_bytes() for p in PUBLIC.iterdir()}; build(); self.assertEqual(first,{p.name:p.read_bytes() for p in PUBLIC.iterdir()})
    def test_T03_unique_date(self): self.assertEqual(len(re.findall(r'\b\d{4}-\d{2}-\d{2}\b',self.notice)),1)
    def test_T04_day_17(self): self.assertEqual(parse_release_key(self.notice)[0].day,17)
    def test_T05_modulo_key(self): self.assertEqual(self.key,parse_release_key(self.notice)[0].day%26)
    def test_T06_key_range(self): self.assertTrue(1<=self.key<=25)
    def test_T07_strict_base64(self): self.assertEqual(base64.b64encode(base64.b64decode(self.raw[:-1],validate=True))+b'\n',self.raw)
    def test_T08_base64_decode(self): self.assertEqual(decode_ciphertext(self.raw),caesar_ascii(plaintext(),self.key))
    def test_T09_uppercase(self): self.assertEqual(caesar_ascii('AZ',1),'BA')
    def test_T10_lowercase(self): self.assertEqual(caesar_ascii('az',1),'ba')
    def test_T11_wrap(self): self.assertEqual(caesar_ascii('Zz',2),'Bb')
    def test_T12_digits(self): self.assertEqual(caesar_ascii('2026-10-17',17),'2026-10-17')
    def test_T13_punctuation(self): self.assertEqual(caesar_ascii(': /;!?.',17),': /;!?.')
    def test_T14_braces_underscores(self): self.assertEqual(caesar_ascii('{_}',17),'{_}')
    def test_T15_reverse(self): self.assertEqual(reverse_ascii_shift(caesar_ascii('Az zA 4_{}',17),17),'Az zA 4_{}')
    def test_T16_round_trip(self): self.assertEqual(reverse_ascii_shift(decode_ciphertext(self.raw),self.key),plaintext())
    def test_T17_unique_flag(self):
        text,flag,_=solve(); self.assertEqual(flag,self.flag); self.assertEqual(len(re.findall(r'MT\{mt03_[a-z0-9_]+\}',text)),1)
    def test_T18_public_only(self):
        with tempfile.TemporaryDirectory(prefix='mt03-public-only-') as d:
            d=Path(d)
            for p in PUBLIC.iterdir(): shutil.copy2(p,d/p.name)
            self.assertEqual(solve(d)[1],self.flag)
    def test_T19_wrong_key(self): self.assertNotIn(self.flag,reverse_ascii_shift(decode_ciphertext(self.raw),(self.key+1)%26))
    def test_T20_wrong_order(self):
        wrong_bytes=reverse_ascii_shift(self.raw.decode(),self.key).encode()
        try: wrong=base64.b64decode(wrong_bytes,validate=True).decode('utf-8')
        except (binascii.Error,UnicodeDecodeError): return
        self.assertNotEqual(wrong,plaintext())
    def test_T21_truncated(self):
        with self.assertRaises(ValueError): decode_ciphertext(self.raw[:-2]+b'\n')
    def test_T22_invalid(self):
        with self.assertRaises(ValueError): decode_ciphertext(b'not*base64\n')
    def test_T23_flag_format(self): self.assertRegex(self.flag,r'^MT\{mt03_[a-z0-9_]+\}$')
    def test_T24_no_notice_flag(self): self.assertNotIn(self.flag,self.notice)
    def test_T25_no_readme_flag(self): self.assertNotIn(self.flag,(PUBLIC/'README.txt').read_text())
    def test_T26_checksum(self): self.assertEqual(subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=PUBLIC,capture_output=True).returncode,0)
    def test_T27_no_private(self): self.assertFalse({p.name for p in PUBLIC.iterdir()}&{'flag.txt','plaintext.txt','solution.md','challenge_config.md'})
    def test_T28_no_credentials(self):
        text='\n'.join(p.read_text() for p in PUBLIC.iterdir() if p.suffix=='.txt' or p.name=='SHA256SUMS')
        self.assertNotRegex(text,r'(?i)(?:SECRET_KEY|password|api[_ -]?token)\s*[:=]')

if __name__=='__main__': unittest.main()
