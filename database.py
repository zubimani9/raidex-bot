import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("RAIDEX_DB_PATH", "/tmp/raidex.db")


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA busy_timeout=20000")
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                pro_until TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id TEXT NOT NULL,
                stars INTEGER NOT NULL,
                payload TEXT NOT NULL,
                telegram_charge_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_user(user_id, username, first_name):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name
        """, (user_id, username, first_name))
        conn.commit()


def get_pro_until(user_id):
    with _connect() as conn:
        row = conn.execute(
            "SELECT pro_until FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    if not row or not row[0]:
        return None

    try:
        until = datetime.fromisoformat(row[0])
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)

        if until <= datetime.now(timezone.utc):
            return None

        return until.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return row[0]


def activate_pro(user_id, days):
    now = datetime.now(timezone.utc)

    current = get_pro_until(user_id)
    if current:
        try:
            base = datetime.strptime(
                current, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            if base > now:
                now = base
        except ValueError:
            pass

    until = now + timedelta(days=days)
    value = until.strftime("%Y-%m-%d %H:%M:%S")

    with _connect() as conn:
        conn.execute(
            "UPDATE users SET pro_until = ? WHERE user_id = ?",
            (value, user_id)
        )
        conn.commit()

    return value


def save_payment(user_id, plan_id, stars, payload, telegram_charge_id):
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with _connect() as conn:
        conn.execute("""
            INSERT INTO payments
            (user_id, plan_id, stars, payload, telegram_charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            plan_id,
            stars,
            payload,
            telegram_charge_id,
            created,
        ))
        conn.commit()
