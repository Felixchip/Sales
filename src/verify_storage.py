import sqlite3
import time

DB_PATH = "verify.db"


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            email TEXT PRIMARY KEY,
            syntax INTEGER,
            has_mx INTEGER,
            smtp_status TEXT,
            smtp_code INTEGER,
            catch_all INTEGER,
            disposable INTEGER,
            role INTEGER,
            score INTEGER,
            verified_at INTEGER
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS saved_emails (
            email TEXT PRIMARY KEY,
            name TEXT,
            score INTEGER,
            saved_at INTEGER
        )
        """)
        
        cols = [d[1] for d in c.execute("PRAGMA table_info(saved_emails)")]
        if 'name' not in cols:
            c.execute("ALTER TABLE saved_emails ADD COLUMN name TEXT")
        
        c.commit()


def save_result(r: dict):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            INSERT INTO verifications (email, syntax, has_mx, smtp_status, smtp_code, catch_all, disposable, role, score, verified_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(email) DO UPDATE SET
                syntax=excluded.syntax,
                has_mx=excluded.has_mx,
                smtp_status=excluded.smtp_status,
                smtp_code=excluded.smtp_code,
                catch_all=excluded.catch_all,
                disposable=excluded.disposable,
                role=excluded.role,
                score=excluded.score,
                verified_at=excluded.verified_at
        """, (
            r["email"],
            int(r["syntax"]),
            int(r["has_mx"]),
            r["smtp_status"],
            r["smtp_code"] if r["smtp_code"] is not None else None,
            int(r["catch_all"]),
            int(r["disposable"]),
            int(r["role"]),
            r["score"],
            int(time.time())
        ))
        c.commit()


def get_result(email: str):
    with sqlite3.connect(DB_PATH) as c:
        row = c.execute("SELECT * FROM verifications WHERE email=?", (email,)).fetchone()
        if not row: 
            return None
        cols = [d[1] for d in c.execute("PRAGMA table_info(verifications)")]
        return dict(zip(cols, row))


def get_all_results(limit=100):
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute("SELECT * FROM verifications ORDER BY verified_at DESC LIMIT ?", (limit,)).fetchall()
        cols = [d[1] for d in c.execute("PRAGMA table_info(verifications)")]
        return [dict(zip(cols, row)) for row in rows]


def save_email(email: str, score: int, name: str = None):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            INSERT INTO saved_emails (email, name, score, saved_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                score=excluded.score
        """, (email, name, score, int(time.time())))
        c.commit()


def get_saved_emails(limit=1000):
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute("SELECT * FROM saved_emails ORDER BY saved_at DESC LIMIT ?", (limit,)).fetchall()
        cols = [d[1] for d in c.execute("PRAGMA table_info(saved_emails)")]
        return [dict(zip(cols, row)) for row in rows]


def delete_saved_email(email: str):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("DELETE FROM saved_emails WHERE email=?", (email,))
        c.commit()


def is_email_saved(email: str):
    with sqlite3.connect(DB_PATH) as c:
        row = c.execute("SELECT 1 FROM saved_emails WHERE email=?", (email,)).fetchone()
        return row is not None
