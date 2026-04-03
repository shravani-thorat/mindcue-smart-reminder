"""
ml_model.py
───────────
Logistic Regression from scratch (no sklearn) to predict task completion
probability given engineered features from behavior history.

Features used (all numeric, normalised internally):
  f0  completion_rate      — completed / (completed + missed)
  f1  avg_completion_hour  — mean hour tasks were completed
  f2  on_time_rate         — fraction completed within ±30 min of schedule
  f3  streak               — current consecutive-day completion streak
  f4  recency_score        — exponential decay weight of recent completions
  f5  miss_streak          — recent consecutive missed days
"""

import math
from database.db import get_connection


# ── Sigmoid & helpers ─────────────────────────────────────────────────────────

def _sigmoid(z: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-z))
    except OverflowError:
        return 0.0 if z < 0 else 1.0


# Pre-trained weights (derived from synthetic calibration data so the model
# gives sensible outputs even with sparse real history).
# Format: [w0..w5, bias]
_WEIGHTS = [
    1.8,    # completion_rate       — strong positive signal
    0.02,   # avg_completion_hour   — slight late-night penalty
   -0.4,    # on_time_rate          — negative: late completion is still done
    0.5,    # streak                — momentum matters
    0.9,    # recency_score         — recent behaviour predicts future
   -1.2,    # miss_streak           — recent misses drag probability down
]
_BIAS = -0.3  # slight conservative prior


# ── Feature extraction ────────────────────────────────────────────────────────

def _extract_features(task_id: int) -> list[float] | None:
    conn = get_connection()
    try:
        history = conn.execute(
            """SELECT completion_hour, was_on_time, completed_at
               FROM task_history WHERE task_id = ?
               ORDER BY completed_at DESC""",
            (task_id,),
        ).fetchall()

        behavior = conn.execute(
            """SELECT event_type, logged_at FROM behavior_log
               WHERE task_id = ? ORDER BY logged_at DESC""",
            (task_id,),
        ).fetchall()
    finally:
        conn.close()

    if not behavior:
        return None  # no data → fall back to heuristic

    total       = len(behavior)
    completions = sum(1 for r in behavior if r["event_type"] == "completed")
    misses      = sum(1 for r in behavior if r["event_type"] == "missed")

    # f0 — completion rate
    f0 = completions / total if total else 0.5

    # f1 — avg completion hour (0-23, normalised to 0-1)
    hours = [r["completion_hour"] for r in history if r["completion_hour"] is not None]
    f1 = (sum(hours) / len(hours) / 23.0) if hours else 0.5

    # f2 — on-time rate
    on_times = [r["was_on_time"] for r in history if r["was_on_time"] is not None]
    f2 = (sum(on_times) / len(on_times)) if on_times else 0.5

    # f3 — current streak (consecutive recent completions)
    streak = 0
    for r in behavior[:10]:
        if r["event_type"] == "completed":
            streak += 1
        else:
            break
    f3 = min(streak / 7.0, 1.0)  # normalise: 7-day streak → 1.0

    # f4 — recency score: exponential decay over last 10 events
    recency = 0.0
    for i, r in enumerate(behavior[:10]):
        weight = math.exp(-0.3 * i)
        recency += weight * (1.0 if r["event_type"] == "completed" else 0.0)
    max_recency = sum(math.exp(-0.3 * i) for i in range(10))
    f4 = recency / max_recency if max_recency else 0.5

    # f5 — miss streak (recent consecutive misses, normalised)
    miss_streak = 0
    for r in behavior[:7]:
        if r["event_type"] == "missed":
            miss_streak += 1
        else:
            break
    f5 = min(miss_streak / 5.0, 1.0)

    return [f0, f1, f2, f3, f4, f5]


# ── Public API ────────────────────────────────────────────────────────────────

def predict_completion_probability(task_id: int) -> dict:
    """
    Returns a dict with:
      probability  — float 0-1
      label        — 'High' | 'Medium' | 'Low'
      features     — dict of named features (for UI transparency)
      model        — 'logistic_regression' | 'heuristic_fallback'
    """
    features = _extract_features(task_id)

    if features is None:
        # No history — return a neutral prior
        return {
            "probability": 0.50,
            "label": "Medium",
            "features": {},
            "model": "heuristic_fallback",
            "note": "No history yet — using neutral prior.",
        }

    f0, f1, f2, f3, f4, f5 = features

    # Linear combination
    z = _BIAS
    for w, f in zip(_WEIGHTS, features):
        z += w * f

    prob = round(_sigmoid(z), 3)

    label = "High" if prob >= 0.70 else "Medium" if prob >= 0.40 else "Low"

    return {
        "probability": prob,
        "label": label,
        "features": {
            "completion_rate":     round(f0, 3),
            "avg_completion_hour": round(f1 * 23, 1),
            "on_time_rate":        round(f2, 3),
            "streak_score":        round(f3, 3),
            "recency_score":       round(f4, 3),
            "miss_streak_score":   round(f5, 3),
        },
        "model": "logistic_regression",
    }
