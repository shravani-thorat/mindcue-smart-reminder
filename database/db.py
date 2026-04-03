import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "reminder.db")


def get_connection():
    """Return a new SQLite connection with row_factory for dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            description     TEXT,
            scheduled_time  TEXT    NOT NULL,
            frequency       TEXT    NOT NULL DEFAULT 'daily',
            priority        INTEGER NOT NULL DEFAULT 1,
            is_active       INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Task completion history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            completed_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            completion_hour INTEGER,
            was_on_time     INTEGER,
            notes           TEXT
        )
    """)

    # Behavior / missed-task tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            event_type  TEXT    NOT NULL,
            logged_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            extra_data  TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialised.")
