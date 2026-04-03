"""
Task service: CRUD operations for tasks and history.
"""

from datetime import datetime
from database.db import get_connection


# ─── Tasks ────────────────────────────────────────────────────────────────────

def create_task(title, scheduled_time, frequency="daily", description=None, priority=1):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO tasks (title, description, scheduled_time, frequency, priority)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, scheduled_time, frequency, priority),
        )
        conn.commit()
        return get_task_by_id(cur.lastrowid)
    finally:
        conn.close()


def get_all_tasks():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE is_active = 1 ORDER BY priority DESC, scheduled_time"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_task_by_id(task_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_task(task_id, **fields):
    allowed = {"title", "description", "scheduled_time", "frequency", "priority"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_task_by_id(task_id)
    clauses = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE tasks SET {clauses} WHERE id = ?", values)
        conn.commit()
        return get_task_by_id(task_id)
    finally:
        conn.close()


def delete_task(task_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ─── History / completion ─────────────────────────────────────────────────────

def mark_task_complete(task_id, notes=None):
    task = get_task_by_id(task_id)
    if not task:
        return None, "Task not found"

    now = datetime.now()
    completion_hour = now.hour

    # Check on-time: within 30 min of scheduled_time
    try:
        sched_h, sched_m = map(int, task["scheduled_time"].split(":"))
        sched_minutes = sched_h * 60 + sched_m
        actual_minutes = now.hour * 60 + now.minute
        was_on_time = 1 if abs(actual_minutes - sched_minutes) <= 30 else 0
    except Exception:
        was_on_time = None

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO task_history (task_id, completed_at, completion_hour, was_on_time, notes)
               VALUES (?, datetime('now'), ?, ?, ?)""",
            (task_id, completion_hour, was_on_time, notes),
        )
        conn.execute(
            "INSERT INTO behavior_log (task_id, event_type) VALUES (?, 'completed')",
            (task_id,),
        )
        conn.commit()
        return {"task": task, "completed_at": now.isoformat(), "was_on_time": was_on_time}, None
    finally:
        conn.close()


def log_missed_task(task_id):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO behavior_log (task_id, event_type) VALUES (?, 'missed')",
            (task_id,),
        )
        # Increase priority by 1 (max 5)
        conn.execute(
            "UPDATE tasks SET priority = MIN(priority + 1, 5) WHERE id = ?",
            (task_id,),
        )
        conn.commit()
    finally:
        conn.close()


def get_task_history(task_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM task_history WHERE task_id = ? ORDER BY completed_at DESC",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
