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
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                pro_until TEXT,
                ref_by INTEGER,
                aff_stars INTEGER DEFAULT 0
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan TEXT,
                stars INTEGER,
                payload TEXT,
                charge_id TEXT,
                created_at TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS raids (
                chat_id INTEGER PRIMARY KEY,
                url TEXT,
                likes INTEGER,
                comments INTEGER,
                reposts INTEGER,
                active INTEGER,
                started_by INTEGER,
                ts REAL,
                file_id TEXT,
                media_type TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS checks (
                chat_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS group_media (
                chat_id INTEGER PRIMARY KEY,
                file_id TEXT,
                media_type TEXT
            )"""
        )
        cols = {row["name"] for row in c.execute("PRAGMA table_info(users)")}
        if "ref_by" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN ref_by INTEGER")
        if "aff_stars" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN aff_stars INTEGER DEFAULT 0")
        raid_cols = {row["name"] for row in c.execute("PRAGMA table_info(raids)")}
        if raid_cols:
            if "file_id" not in raid_cols:
                c.execute("ALTER TABLE raids ADD COLUMN file_id TEXT")
            if "media_type" not in raid_cols:
                c.execute("ALTER TABLE raids ADD COLUMN media_type TEXT")


def save_user(user_id, username, first_name, ref_by=None):
    with conn() as c:
        row = c.execute("SELECT user_id, ref_by FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            c.execute(
                """UPDATE users SET username=?, first_name=? WHERE user_id=?""",
                (username, first_name, user_id),
            )
        else:
            if ref_by == user_id:
                ref_by = None
            c.execute(
                """INSERT INTO users(user_id, username, first_name, ref_by, aff_stars)
                   VALUES(?,?,?,?,0)""",
                (user_id, username, first_name, ref_by),
            )


def get_user(user_id):
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def is_pro(user_id):
    until = get_pro_until(user_id)
    if not until:
        return False
    try:
        return datetime.fromisoformat(until) > datetime.now(timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(until, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
        except ValueError:
            return False


def get_pro_until(user_id):
    with conn() as c:
        row = c.execute("SELECT pro_until FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["pro_until"] if row and row["pro_until"] else None


def activate_pro(user_id, days):
    now = datetime.now(timezone.utc)
    current = get_pro_until(user_id)
    if current:
        for fmt in (None, "%Y-%m-%d %H:%M:%S"):
            try:
                old = datetime.fromisoformat(current) if fmt is None else datetime.strptime(current, fmt).replace(tzinfo=timezone.utc)
                if old.tzinfo is None:
                    old = old.replace(tzinfo=timezone.utc)
                if old > now:
                    now = old
                break
            except ValueError:
                continue
    until = now + timedelta(days=days)
    value = until.strftime("%Y-%m-%d %H:%M:%S")
    with conn() as c:
        exists = c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
        if exists:
            c.execute("UPDATE users SET pro_until=? WHERE user_id=?", (value, user_id))
        else:
            c.execute(
                "INSERT INTO users(user_id, pro_until, aff_stars) VALUES(?,?,0)",
                (user_id, value),
            )
    return value


def save_payment(user_id, plan, stars, payload, charge_id):
    with conn() as c:
        c.execute(
            """INSERT INTO payments
               (user_id, plan, stars, payload, charge_id, created_at)
               VALUES(?,?,?,?,?,?)""",
            (user_id, plan, stars, payload, charge_id, datetime.now(timezone.utc).isoformat()),
        )


def add_affiliate_stars(user_id, stars):
    with conn() as c:
        c.execute(
            "UPDATE users SET aff_stars = COALESCE(aff_stars,0) + ? WHERE user_id=?",
            (stars, user_id),
        )


def affiliate_stats(user_id):
    with conn() as c:
        row = c.execute("SELECT aff_stars FROM users WHERE user_id=?", (user_id,)).fetchone()
        refs = c.execute("SELECT COUNT(*) AS n FROM users WHERE ref_by=?", (user_id,)).fetchone()["n"]
        return (row["aff_stars"] if row and row["aff_stars"] else 0), refs


def set_group_media(chat_id, file_id, media_type):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO group_media(chat_id, file_id, media_type) VALUES(?,?,?)",
            (chat_id, file_id, media_type),
        )


def get_group_media(chat_id):
    with conn() as c:
        return c.execute(
            "SELECT file_id, media_type FROM group_media WHERE chat_id=?",
            (chat_id,),
        ).fetchone()


def clear_group_media(chat_id):
    with conn() as c:
        c.execute("DELETE FROM group_media WHERE chat_id=?", (chat_id,))


def save_raid(chat_id, url, likes, comments, reposts, started_by, file_id, media_type):
    with conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO raids
               (chat_id, url, likes, comments, reposts, active, started_by, ts, file_id, media_type)
               VALUES(?,?,?,?,?,1,?,?,?,?)""",
            (chat_id, url, likes, comments, reposts, started_by, datetime.now(timezone.utc).timestamp(), file_id, media_type),
        )
        c.execute("DELETE FROM checks WHERE chat_id=?", (chat_id,))


def stop_raid(chat_id):
    with conn() as c:
        c.execute("UPDATE raids SET active=0 WHERE chat_id=?", (chat_id,))


def get_active_raid(chat_id):
    with conn() as c:
        return c.execute(
            "SELECT * FROM raids WHERE chat_id=? AND active=1",
            (chat_id,),
        ).fetchone()


def add_check(chat_id, user_id):
    with conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO checks(chat_id, user_id) VALUES(?,?)",
            (chat_id, user_id),
        )
        n = c.execute("SELECT COUNT(*) AS n FROM checks WHERE chat_id=?", (chat_id,)).fetchone()["n"]
        return n


def raid_checks(chat_id, limit=20):
    with conn() as c:
        return c.execute(
            "SELECT user_id FROM checks WHERE chat_id=? LIMIT ?",
            (chat_id, limit),
        ).fetchall()
