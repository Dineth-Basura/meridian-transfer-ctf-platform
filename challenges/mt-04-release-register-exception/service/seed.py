"""Deterministic synthetic release-register seed; author build only."""
import hashlib
import hmac
import sqlite3
from pathlib import Path

SOURCE_ID = 'MERIDIAN-MT04-V1'
ITERATIONS = 260_000
PARTICIPANT = 'case_reviewer'
TARGET_ID = 1047
OWN_IDS = (1041, 1042)

def training_password(username: str) -> str:
    return 'Lab-' + hashlib.sha256(f'{SOURCE_ID}:credential:{username}'.encode()).hexdigest()[:16]

def flag() -> str:
    suffix = hashlib.sha256(f'{SOURCE_ID}:restricted-export'.encode()).hexdigest()[:7]
    return f'MT{{mt04_quay_export_{suffix}}}'

def password_hash(password: str, username: str) -> str:
    salt = hashlib.sha256(f'{SOURCE_ID}:salt:{username}'.encode()).digest()[:16]
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split('$')
        if algorithm != 'pbkdf2_sha256' or int(iterations) < 200_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def create_seed(path: Path) -> None:
    path = Path(path)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    try:
        conn.execute('PRAGMA page_size=4096')
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.executescript('''
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE releases (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            transfer_reference TEXT NOT NULL,
            project_code TEXT NOT NULL,
            destination TEXT NOT NULL,
            release_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            summary TEXT NOT NULL,
            related_record_id INTEGER,
            export_note TEXT NOT NULL
        );
        ''')
        users = [(1,PARTICIPANT),(2,'archive_clerk'),(3,'restricted_custodian')]
        conn.executemany('INSERT INTO users VALUES (?,?,?)',[(uid,name,password_hash(training_password(name),name)) for uid,name in users])
        records = [
            (1041,1,'MT-RR-1041','ORCHID-7','Local quay desk','Approved','2026-11-04T09:00:00Z','Handover review packet assigned to the training account.',TARGET_ID,'Routine export: handover review packet.\n'),
            (1042,1,'MT-RR-1042','PINE-2','Archive shelf B','Pending','2026-11-04T09:15:00Z','Secondary packet awaiting a desk signature.',None,'Routine export: secondary packet.\n'),
            (1043,2,'MT-RR-1043','LARK-8','Fictional archive','Approved','2026-11-03T13:30:00Z','Clerk reference unrelated to the current review.',None,'Routine export: clerk packet.\n'),
            (1044,2,'MT-RR-1044','MOSS-3','Fictional depot','Pending','2026-11-02T08:20:00Z','Decoy release for normal ownership checks.',None,'Routine export: depot packet.\n'),
            (TARGET_ID,3,'MT-RR-1047','QUAY-9','Restricted desk','Exception review','2026-11-04T10:05:00Z','Release exception associated with the handover discrepancy.',None,f'Release exception: restricted synthetic record.\nVerification: {flag()}\n'),
        ]
        conn.executemany('INSERT INTO releases VALUES (?,?,?,?,?,?,?,?,?,?)',records)
        conn.commit()
        conn.execute('VACUUM')
    finally:
        conn.close()
