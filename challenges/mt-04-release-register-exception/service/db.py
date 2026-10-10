"""Read-only immutable SQLite access for the release register."""
import sqlite3
from contextlib import closing
from pathlib import Path
from flask import current_app

def connect():
    path = Path(current_app.config['SEED_DB_PATH']).resolve()
    connection = sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA query_only=ON')
    return connection

def user_by_name(username):
    with closing(connect()) as db:
        row = db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        return dict(row) if row else None

def user_by_id(user_id):
    with closing(connect()) as db:
        row = db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
        return dict(row) if row else None

def owned_releases(user_id):
    with closing(connect()) as db:
        return [dict(row) for row in db.execute('SELECT id,transfer_reference,project_code,destination,release_status,created_at,summary,related_record_id FROM releases WHERE owner_id=? ORDER BY id',(user_id,)).fetchall()]

def release_by_id(record_id):
    with closing(connect()) as db:
        row = db.execute('SELECT * FROM releases WHERE id=?',(record_id,)).fetchone()
        return dict(row) if row else None
