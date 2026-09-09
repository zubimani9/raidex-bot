import sqlite3
from datetime import datetime, timedelta, timezone
DB_PATH='/tmp/raidex.db'
def connect():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, pro_until TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,plan TEXT,stars INTEGER,payload TEXT UNIQUE,telegram_charge_id TEXT UNIQUE,paid_at TEXT)')
        c.commit()
def save_user(uid,username,first_name):
    with connect() as c:
        c.execute('INSERT INTO users VALUES (?,?,?,NULL) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name',(uid,username,first_name)); c.commit()
def activate_pro(uid,days):
    now=datetime.now(timezone.utc)
    with connect() as c:
        r=c.execute('SELECT pro_until FROM users WHERE user_id=?',(uid,)).fetchone(); base=now
        if r and r['pro_until']:
            try:
                x=datetime.fromisoformat(r['pro_until']); base=max(now,x)
            except ValueError: pass
        until=(base+timedelta(days=days)).replace(microsecond=0).isoformat()
        c.execute('UPDATE users SET pro_until=? WHERE user_id=?',(until,uid)); c.commit(); return until
def save_payment(uid,plan,stars,payload,charge):
    with connect() as c:
        c.execute('INSERT OR IGNORE INTO payments(user_id,plan,stars,payload,telegram_charge_id,paid_at) VALUES(?,?,?,?,?,?)',(uid,plan,stars,payload,charge,datetime.now(timezone.utc).replace(microsecond=0).isoformat())); c.commit()
def get_pro_until(uid):
    with connect() as c: r=c.execute('SELECT pro_until FROM users WHERE user_id=?',(uid,)).fetchone()
    if not r or not r['pro_until']: return None
    try:
        x=datetime.fromisoformat(r['pro_until'])
        return r['pro_until'] if x>datetime.now(timezone.utc) else None
    except ValueError: return None
