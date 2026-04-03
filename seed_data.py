"""
Seed the database with sample tasks and fake history for demo purposes.
Run: python seed_data.py
"""

import sqlite3
import random
from datetime import datetime, timedelta
from database.db import init_db, get_connection

TASKS = [
    ("Morning Workout", "07:00", "daily", "30 min cardio + stretching", 3),
    ("Take Vitamins", "08:30", "daily", "Vitamin D and Omega-3", 2),
    ("Deep Work Block", "09:00", "daily", "Focus session, no distractions", 4),
    ("Team Standup", "10:00", "daily", "15-min sync with the team", 5),
    ("Read 20 Pages", "21:00", "daily", "Non-fiction reading habit", 2),
    ("Weekly Review", "18:00", "weekly", "Review goals and plan next week", 3),
    ("Meal Prep", "16:00", "weekly", "Prep meals for the week", 3),
]

def seed():
    init_db()
    conn = get_connection()
    # Clear existing data
    conn.execute("DELETE FROM behavior_log")
    conn.execute("DELETE FROM task_history")
    conn.execute("DELETE FROM tasks")
    conn.commit()

    task_ids = []
    for title, stime, freq, desc, prio in TASKS:
        cur = conn.execute(
            "INSERT INTO tasks (title, scheduled_time, frequency, description, priority) VALUES (?,?,?,?,?)",
            (title, stime, freq, desc, prio)
        )
        task_ids.append((cur.lastrowid, int(stime.split(":")[0])))
    conn.commit()

    # Generate fake completion history (past 14 days)
    for task_id, sched_hour in task_ids:
        for days_ago in range(1, 15):
            if random.random() < 0.7:  # 70% completion rate
                dt = datetime.now() - timedelta(days=days_ago)
                # Usually complete within ±1 hour of scheduled time
                hour_offset = random.randint(-1, 2)
                actual_hour = max(0, min(23, sched_hour + hour_offset))
                completed_at = dt.replace(hour=actual_hour, minute=random.randint(0, 59))
                was_on_time = 1 if abs(actual_hour - sched_hour) <= 0 else 0
                conn.execute(
                    "INSERT INTO task_history (task_id, completed_at, completion_hour, was_on_time) VALUES (?,?,?,?)",
                    (task_id, completed_at.isoformat(), actual_hour, was_on_time)
                )
                conn.execute("INSERT INTO behavior_log (task_id, event_type) VALUES (?, 'completed')", (task_id,))
            else:
                # Mark as missed, potentially increase priority
                conn.execute("INSERT INTO behavior_log (task_id, event_type) VALUES (?, 'missed')", (task_id,))

    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(TASKS)} tasks with 14 days of history.")

if __name__ == "__main__":
    seed()
