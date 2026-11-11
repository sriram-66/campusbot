import sqlite3
from . import config


def _conn():
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def save_message(session_id: str, role: str, content: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_history(session_id: str, limit: int = 6):
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE session_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [{"role": r, "content": t} for r, t in reversed(rows)]


def init_feedback():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT,
                answer TEXT,
                rating INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def save_feedback(session_id: str, question: str, answer: str, rating: int):
    with _conn() as c:
        c.execute(
            "INSERT INTO feedback (session_id, question, answer, rating) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, rating),
        )


def feedback_stats():
    with _conn() as c:
        up = c.execute("SELECT COUNT(*) FROM feedback WHERE rating = 1").fetchone()[0]
        down = c.execute("SELECT COUNT(*) FROM feedback WHERE rating = -1").fetchone()[0]
        bad = c.execute(
            "SELECT question, created_at FROM feedback WHERE rating = -1 "
            "ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return {"up": up, "down": down, "recent_bad": [{"question": q, "at": t} for q, t in bad]}
