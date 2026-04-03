# MindCue — Memory-Based Smart Reminder Engine

A full-stack intelligent reminder system that **learns your habits** and suggests optimal reminder times based on your past completion behaviour.

## Features

| Feature | Description |
|---|---|
| **Task CRUD** | Add, view, edit, and delete tasks |
| **Frequency support** | Daily, weekly, or custom schedules |
| **Priority scoring** | 1–5 priority levels; auto-escalates on missed tasks |
| **Completion tracking** | Timestamped history with on-time detection |
| **Missed task detection** | Logs misses and boosts priority automatically |
| **Smart recommendations** | Suggests reminders 10–15 min before your usual completion time |
| **Completion probability** | Heuristic model (0–1) based on history and missed events |
| **Insights** | Human-readable pattern summaries per task |
| **Notification simulation** | Visual banner showing reminder logic |

---

## Tech Stack

- **Backend:** Python 3.11 + Flask 3
- **Database:** SQLite (zero-config, file-based)
- **Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
- **Deployment:** Render (free tier via gunicorn)

---

## Project Structure

```
smart-reminder/
├── app.py                  # Flask entry point
├── requirements.txt
├── Procfile                # Render/gunicorn startup
├── seed_data.py            # Demo data generator
├── database/
│   ├── __init__.py
│   └── db.py               # Connection + schema init
├── models/
│   └── task.py             # Task dataclass
├── routes/
│   ├── task_routes.py      # CRUD + complete/missed endpoints
│   └── recommendation_routes.py
├── services/
│   ├── task_service.py     # Business logic for tasks
│   └── recommendation_service.py  # Recommendation engine
└── templates/
    └── index.html          # SPA frontend
```

---

##  Sample Data

Run `python seed_data.py` to populate 7 tasks with 14 days of simulated completion history, enabling the recommendation engine to surface meaningful insights immediately.

---

##  Database Schema

```sql
-- Tasks
CREATE TABLE tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT,
    scheduled_time  TEXT NOT NULL,       -- "HH:MM"
    frequency       TEXT NOT NULL,       -- daily | weekly | custom
    priority        INTEGER DEFAULT 1,   -- 1 (low) to 5 (high)
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Completion history
CREATE TABLE task_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    completed_at    TEXT DEFAULT (datetime('now')),
    completion_hour INTEGER,
    was_on_time     INTEGER,    -- 1 = within ±30 min of schedule
    notes           TEXT
);

-- Behaviour log (completions, misses, snoozes)
CREATE TABLE behavior_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL,   -- completed | missed | snoozed
    logged_at   TEXT DEFAULT (datetime('now')),
    extra_data  TEXT
);
```

---

## 🧠 How the Recommendation Engine Works

1. **Pattern detection** — counts completion hours from `task_history`, finds the most frequent hour
2. **Reminder suggestion** — sets reminder 15 min before the most common completion time
3. **Missed task escalation** — each miss increments priority (floor 1, ceil 5) via `behavior_log`
4. **Completion probability** — heuristic score: base 0.5 + completions bonus − misses penalty + on-time rate boost
5. **Human insights** — plain-English summary strings generated from the above data

---

Made by shravani thorat — beginner-friendly, production-structured.
