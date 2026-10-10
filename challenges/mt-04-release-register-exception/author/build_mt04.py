#!/usr/bin/env python3
"""Build immutable synthetic MT-04 seed and private author credentials."""
from pathlib import Path
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'service'))
from seed import create_seed, training_password, flag, PARTICIPANT, TARGET_ID
import sqlite3


def build():
    private = ROOT/'private'; data = ROOT/'service/data'
    private.mkdir(exist_ok=True); data.mkdir(exist_ok=True)
    value = flag()
    if not re.fullmatch(r'MT\{mt04_[a-z0-9_]+\}', value):
        raise ValueError('Invalid flag format')
    path = data/'seed.sqlite'
    create_seed(path)
    with sqlite3.connect(path) as db:
        users=db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        participant_records=db.execute('SELECT COUNT(*) FROM releases WHERE owner_id=1').fetchone()[0]
        target=db.execute('SELECT owner_id,export_note FROM releases WHERE id=?',(TARGET_ID,)).fetchone()
        all_notes='\n'.join(row[0] for row in db.execute('SELECT export_note FROM releases'))
    if users<3 or participant_records<2 or target[0]==1 or all_notes.count(value)!=1:
        raise AssertionError('Seed records or flag placement invalid')
    (private/'flag.txt').write_text(value+'\n')
    (private/'flag.txt').chmod(0o600)
    (private/'credentials.txt').write_text(f'username={PARTICIPANT}\npassword={training_password(PARTICIPANT)}\n')
    (private/'credentials.txt').chmod(0o600)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (private/'seed_sha256.txt').write_text(digest+'  seed.sqlite\n')
    print('MT-04 deterministic seed built; SHA-256',digest)
    return digest
if __name__=='__main__': build()
