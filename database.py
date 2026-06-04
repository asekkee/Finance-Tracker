import sqlite3
from datetime import datetime, date

DB_PATH = "finance.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создаёт таблицу при первом запуске."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      INTEGER NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_expense(user_id: int, amount: int, category: str, description: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, description, created_at) VALUES (?,?,?,?,?)",
        (user_id, amount, category, description, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_today_expenses(user_id: int) -> list[dict]:
    today = date.today().isoformat()
    conn = get_conn()
    rows = conn.execute(
        "SELECT amount, category, description, created_at FROM expenses "
        "WHERE user_id=? AND created_at LIKE ? ORDER BY created_at DESC",
        (user_id, f"{today}%"),
    ).fetchall()
    conn.close()
    return [{"amount": r[0], "category": r[1], "description": r[2], "created_at": r[3]} for r in rows]


def get_month_expenses(user_id: int) -> list[dict]:
    today = date.today()
    month_prefix = today.strftime("%Y-%m")
    conn = get_conn()
    rows = conn.execute(
        "SELECT amount, category, description, created_at FROM expenses "
        "WHERE user_id=? AND created_at LIKE ? ORDER BY created_at DESC",
        (user_id, f"{month_prefix}%"),
    ).fetchall()
    conn.close()
    return [{"amount": r[0], "category": r[1], "description": r[2], "created_at": r[3]} for r in rows]