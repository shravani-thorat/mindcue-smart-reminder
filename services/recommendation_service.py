"""
recommendation_service.py
─────────────────────────
Combines pattern analysis + the ML model to produce rich recommendations.
"""

from collections import Counter
from database.db import get_connection
from services.ml_model import predict_completion_probability


def _fetch_completion_hours(task_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT completion_hour FROM task_history WHERE task_id = ? AND completion_hour IS NOT NULL",
            (task_id,),
        ).fetchall()
        return [r["completion_hour"] for r in rows]
    finally:
        conn.close()


def _fetch_miss_count(task_id):
    conn = get_connection()
    try:
        r = conn.execute(
            "SELECT COUNT(*) c FROM behavior_log WHERE task_id=? AND event_type='missed'",
            (task_id,),
        ).fetchone()
        return r["c"]
    finally:
        conn.close()


def _fetch_completion_count(task_id):
    conn = get_connection()
    try:
        r = conn.execute(
            "SELECT COUNT(*) c FROM task_history WHERE task_id=?", (task_id,)
        ).fetchone()
        return r["c"]
    finally:
        conn.close()


def _on_time_rate(task_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT was_on_time FROM task_history WHERE task_id=? AND was_on_time IS NOT NULL",
            (task_id,),
        ).fetchall()
        if not rows:
            return None
        return sum(r["was_on_time"] for r in rows) / len(rows)
    finally:
        conn.close()


def _recent_trend(task_id, n=5):
    """Returns 'improving' | 'declining' | 'stable' based on last n events."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT event_type FROM behavior_log WHERE task_id=?
               ORDER BY logged_at DESC LIMIT ?""",
            (task_id, n),
        ).fetchall()
    finally:
        conn.close()
    if len(rows) < 3:
        return "stable"
    events = [r["event_type"] for r in rows]
    recent_score = sum(1 if e == "completed" else -1 for e in events[:3])
    older_score  = sum(1 if e == "completed" else -1 for e in events[3:]) if len(events) > 3 else 0
    if recent_score > older_score:
        return "improving"
    elif recent_score < older_score:
        return "declining"
    return "stable"


def _suggest_reminder(scheduled_time: str, usual_hour: int | None) -> str:
    """Return reminder time string HH:MM, 15 min before usual hour or scheduled time."""
    try:
        if usual_hour is not None:
            total = usual_hour * 60 - 15
        else:
            sh, sm = map(int, scheduled_time.split(":"))
            total = sh * 60 + sm - 15
        total = total % (24 * 60)
        return f"{total // 60:02d}:{total % 60:02d}"
    except Exception:
        return scheduled_time


def get_recommendation_for_task(task: dict) -> dict:
    task_id = task["id"]

    hours            = _fetch_completion_hours(task_id)
    miss_count       = _fetch_miss_count(task_id)
    completion_count = _fetch_completion_count(task_id)
    on_time_rate     = _on_time_rate(task_id)
    trend            = _recent_trend(task_id)
    ml               = predict_completion_probability(task_id)

    insights = []
    usual_hour = None

    # ── Pattern: most common completion hour ────────────────────────────────
    if hours:
        most_common_hour, freq = Counter(hours).most_common(1)[0]
        usual_hour = most_common_hour
        pct = round(freq / len(hours) * 100)
        insights.append(
            f"📊 You usually complete this task around "
            f"{most_common_hour:02d}:00 ({pct}% of the time)."
        )
    else:
        insights.append("🆕 No completion history yet — using scheduled time for reminder.")

    # ── Pattern: missed tasks ────────────────────────────────────────────────
    if miss_count >= 5:
        insights.append(f"🚨 You've missed this task {miss_count} times — it's been escalated to max priority.")
    elif miss_count >= 3:
        insights.append(f"⚠️  You've missed this task {miss_count} times. Priority increased.")
    elif miss_count >= 1:
        insights.append(f"📌 Missed {miss_count} time(s) recently. Keep an eye on this one.")

    # ── Pattern: on-time rate ────────────────────────────────────────────────
    if on_time_rate is not None:
        if on_time_rate >= 0.80:
            insights.append("✅ Excellent punctuality — you complete this on time 80%+ of the time!")
        elif on_time_rate >= 0.50:
            insights.append(f"⏱ On-time rate: {round(on_time_rate*100)}%. Decent — keep it up.")
        else:
            insights.append("⏰ You tend to run late on this task. Consider an earlier reminder.")

    # ── Pattern: trend ───────────────────────────────────────────────────────
    if trend == "improving":
        insights.append("📈 Your recent behaviour is improving — great momentum!")
    elif trend == "declining":
        insights.append("📉 Recent pattern shows declining completions. Time to re-prioritise?")

    # ── ML model insight ─────────────────────────────────────────────────────
    prob = ml["probability"]
    if ml["model"] == "logistic_regression":
        if prob >= 0.75:
            insights.append(f"🤖 ML model predicts {round(prob*100)}% chance you'll complete this — high confidence.")
        elif prob <= 0.35:
            insights.append(f"🤖 ML model flags a low completion probability ({round(prob*100)}%). Extra nudge added.")

    suggested_reminder = _suggest_reminder(task["scheduled_time"], usual_hour)

    return {
        "task_id":                    task_id,
        "task_title":                 task["title"],
        "scheduled_time":             task["scheduled_time"],
        "frequency":                  task["frequency"],
        "suggested_reminder":         suggested_reminder,
        "completion_count":           completion_count,
        "miss_count":                 miss_count,
        "on_time_rate":               round(on_time_rate, 2) if on_time_rate is not None else None,
        "trend":                      trend,
        "priority":                   task["priority"],
        "ml_probability":             ml["probability"],
        "ml_label":                   ml["label"],
        "ml_features":                ml["features"],
        "ml_model":                   ml["model"],
        "insights":                   insights,
    }


def get_all_recommendations() -> list[dict]:
    conn = get_connection()
    try:
        tasks = [dict(r) for r in conn.execute(
            "SELECT * FROM tasks WHERE is_active=1 ORDER BY priority DESC"
        ).fetchall()]
    finally:
        conn.close()
    return [get_recommendation_for_task(t) for t in tasks]
