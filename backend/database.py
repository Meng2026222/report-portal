"""数据库层 — SQLite 存储用户和评论"""
import sqlite3, os, time
from pathlib import Path

DB_PATH = Path(__file__).parent / "portal.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github_id TEXT UNIQUE NOT NULL,
            github_login TEXT NOT NULL,
            avatar_url TEXT DEFAULT '',
            nickname TEXT DEFAULT '',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            nickname TEXT NOT NULL,
            avatar_url TEXT DEFAULT '',
            text TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_comments_company ON comments(company_id, created_at);
    """)
    conn.commit()
    conn.close()

def upsert_user(github_id, github_login, avatar_url):
    conn = get_conn()
    now = time.time()
    existing = conn.execute("SELECT * FROM users WHERE github_id=?", (github_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE users SET github_login=?, avatar_url=? WHERE github_id=?",
            (github_login, avatar_url, github_id)
        )
        conn.commit()
        user_id = existing["id"]
        nickname = existing.get("nickname") or ""
        # Return existing nickname
        conn.close()
        return {"id": user_id, "github_id": github_id, "github_login": github_login,
                "avatar_url": avatar_url, "nickname": nickname or github_login, "is_new": False}
    else:
        conn.execute(
            "INSERT INTO users (github_id, github_login, avatar_url, nickname, created_at) VALUES (?,?,?,?,?)",
            (github_id, github_login, avatar_url, github_login, now)
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return {"id": user_id, "github_id": github_id, "github_login": github_login,
                "avatar_url": avatar_url, "nickname": github_login, "is_new": True}

def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_nickname(user_id, nickname):
    conn = get_conn()
    conn.execute("UPDATE users SET nickname=? WHERE id=?", (nickname[:30], user_id))
    conn.commit()
    conn.close()

def add_comment(company_id, user_id, nickname, avatar_url, text):
    conn = get_conn()
    now = time.time()
    conn.execute(
        "INSERT INTO comments (company_id, user_id, nickname, avatar_url, text, created_at) VALUES (?,?,?,?,?,?)",
        (company_id, user_id, nickname[:30], avatar_url, text[:1000], now)
    )
    conn.commit()
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": cid, "company_id": company_id, "user_id": user_id,
            "nickname": nickname[:30], "avatar_url": avatar_url,
            "text": text[:1000], "created_at": now}

def get_comments(company_id, limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, company_id, user_id, nickname, avatar_url, text, created_at "
        "FROM comments WHERE company_id=? ORDER BY created_at ASC LIMIT ?",
        (company_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Initialize on import
init_db()
