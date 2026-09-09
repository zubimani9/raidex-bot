import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("RAIDEX_DB_PATH", "/tmp/raidex.db")

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            pro_until TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            stars INTEGER,
            payload TEXT,
            charge_id TEXT,
            created_at TEXT
        )""")

def save_user(user_id, username, first_name):
    with conn() as c:
        c.execute("""INSERT INTO users(user_id,username,first_name)
                     VALUES(?,?,?)
                     ON CONFLICT(user_id) DO UPDATE SET
                     username=excluded.username, first_name=excluded.first_name""",
                  (user_id, username, first_name))

def get_pro_until(user_id):
    with conn() as c:
        row = c.execute("SELECT pro_until FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["pro_until"] if row and row["pro_until"] else None

def activate_pro(user_id, days):
    now = datetime.now(timezone.utc)
    current = get_pro_until(user_id)
    if current:
        try:
            old = datetime.fromisoformat(current)
            if old > now:
                now = old
        except ValueError:
            pass
    until = now + timedelta(days=days)
    value = until.strftime("%Y-%m-%d %H:%M:%S")
    with conn() as c:
        c.execute("UPDATE users SET pro_until=? WHERE user_id=?", (value, user_id))
    return value

def save_payment(user_id, plan, stars, payload, charge_id):
    with conn() as c:
        c.execute("""INSERT INTO payments
                     (user_id,plan,stars,payload,charge_id,created_at)
                     VALUES(?,?,?,?,?,?)""",
                  (user_id, plan, stars, payload, charge_id,
                   datetime.now(timezone.utc).isoformat()))
