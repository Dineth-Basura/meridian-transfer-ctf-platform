import hashlib
import importlib.util
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=ROOT/'author'; PUBLIC=ROOT/'public'
sys.path.insert(0,str(AUTHOR))
from build_mt02 import build, make_image, payload_text
from reference_extractor import extract
class MT02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build(); cls.path=PUBLIC/'amended_contact_sheet.png'; cls.flag=(ROOT/'private/flag.txt').read_text().strip(); cls.data=payload_text().encode()
    def test_T01_builder_files(self): self.assertEqual({p.name for p in PUBLIC.iterdir()},{'amended_contact_sheet.png','README.txt','SHA256SUMS'})
    def test_T02_rgb(self):
        with Image.open(self.path) as im: self.assertEqual(im.mode,'RGB')
    def test_T03_capacity(self):
        with Image.open(self.path) as im: self.assertGreater(im.width*im.height,32+len(self.data)*8)
    def test_T04_metadata_clue(self):
        with Image.open(self.path) as im: self.assertIn('lowest-order red image data',im.info['Comment'])
    def test_T05_metadata_no_flag(self):
        with Image.open(self.path) as im: self.assertNotIn(self.flag,str(im.info))
    def test_T06_one_payload(self): self.assertEqual(extract()[1].count('Stage verification:'),1)
    def test_T07_exact_flag(self): self.assertEqual(extract()[2],self.flag)
    def test_T08_big_endian_header(self):
        with Image.open(self.path) as im:
            px=im.load(); bits=[px[i%im.width,i//im.width][0]&1 for i in range(32)]
        self.assertEqual(int(''.join(map(str,bits)),2),len(self.data))
        self.assertEqual(struct.pack('>I',len(self.data)),bytes(int(''.join(map(str,bits[i:i+8])),2) for i in range(0,32,8)))
    def test_T09_utf8(self): self.assertEqual(extract()[1],self.data.decode('utf-8'))
    def test_T10_row_major(self):
        with Image.open(self.path) as im:
            px=im.load(); stream=struct.pack('>I',len(self.data))+self.data
            for i in (0,1,7,8,31,32,im.width-1,im.width,im.width+1,len(stream)*8-1):
                self.assertEqual(px[i%im.width,i//im.width][0]&1,(stream[i//8]>>(7-i%8))&1)
    def test_T11_red_only(self):
        original=make_image()
        with Image.open(self.path) as im:
            self.assertEqual(im.getchannel('G').tobytes(),original.getchannel('G').tobytes())
            self.assertEqual(im.getchannel('B').tobytes(),original.getchannel('B').tobytes())
            for i in range(32+len(self.data)*8):
                x,y=i%im.width,i//im.width
                self.assertEqual(im.getpixel((x,y))[0]&254,original.getpixel((x,y))[0]&254)
    def test_T12_no_plain_flag_chunk(self): self.assertNotIn(self.flag.encode(),self.path.read_bytes())
    def test_T13_checksum(self): self.assertEqual(subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=PUBLIC,capture_output=True).returncode,0)
    def test_T14_repeat_build_hash(self):
        first=hashlib.sha256(self.path.read_bytes()).hexdigest(); build(); self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),first)
    def test_T15_modified_copy_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); shutil.copy(self.path,d/self.path.name); shutil.copy(PUBLIC/'SHA256SUMS',d/'SHA256SUMS')
            with Image.open(d/self.path.name) as im: copy=im.copy()
            copy.putpixel((500,500),(1,2,3)); copy.save(d/self.path.name)
            self.assertNotEqual(subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=d,capture_output=True).returncode,0)
    def test_T16_rebuild_restores(self):
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest(); build(); self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),digest)
    def test_T17_flag_format(self): self.assertRegex(self.flag,r'^MT\{mt02_[a-z0-9_]+\}$')
    def test_T18_readme_no_token(self): self.assertNotIn(self.flag.split('mt02_')[1][:-1],(PUBLIC/'README.txt').read_text())
    def test_T19_no_private(self): self.assertFalse({p.name for p in PUBLIC.iterdir()}&{'flag.txt','payload.txt','solution.md','challenge_config.md'})
    def test_T20_no_credentials(self):
        s='\n'.join(p.read_text() for p in PUBLIC.iterdir() if p.suffix in ('.txt','') or p.name=='SHA256SUMS')
        self.assertNotRegex(s,r'(?i)(SECRET_KEY\s*=|password\s*=|api[_ -]?token\s*=)')
if __name__=='__main__': unittest.main()
