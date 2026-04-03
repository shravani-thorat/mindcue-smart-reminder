# MindCue API Testing Guide

## Base URL
`http://localhost:5000`

All responses: `{"success": true|false, "data": {...} | "error": "message"}`

---

## Tasks

### Create a task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Morning Workout","scheduled_time":"07:00","frequency":"daily","description":"30 min run","priority":3}'
```

### List all tasks
```bash
curl http://localhost:5000/api/tasks
```

### Get single task
```bash
curl http://localhost:5000/api/tasks/1
```

### Update a task
```bash
curl -X PUT http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"scheduled_time":"07:30","priority":4}'
```

### Delete a task
```bash
curl -X DELETE http://localhost:5000/api/tasks/1
```

### Mark complete
```bash
curl -X POST http://localhost:5000/api/tasks/1/complete \
  -H "Content-Type: application/json" \
  -d '{"notes":"Felt great!"}'
```

### Mark missed
```bash
curl -X POST http://localhost:5000/api/tasks/1/missed
```

### Get completion history
```bash
curl http://localhost:5000/api/tasks/1/history
```

---

## Recommendations

### All recommendations
```bash
curl http://localhost:5000/api/recommendations
```

### Single task recommendation
```bash
curl http://localhost:5000/api/recommendations/1
```

### ML model detail (feature vector)
```bash
curl http://localhost:5000/api/recommendations/1/ml
```

#### ML Response example:
```json
{
  "success": true,
  "data": {
    "probability": 0.849,
    "label": "High",
    "model": "logistic_regression",
    "features": {
      "completion_rate": 0.667,
      "avg_completion_hour": 9.5,
      "on_time_rate": 0.3,
      "streak_score": 0.429,
      "recency_score": 0.807,
      "miss_streak_score": 0.0
    }
  }
}
```

---

## Full Recommendation Response Example

```json
{
  "task_id": 1,
  "task_title": "Morning Workout",
  "scheduled_time": "07:00",
  "suggested_reminder": "06:45",
  "completion_count": 9,
  "miss_count": 4,
  "on_time_rate": 0.44,
  "trend": "improving",
  "priority": 3,
  "ml_probability": 0.76,
  "ml_label": "High",
  "ml_model": "logistic_regression",
  "ml_features": { "completion_rate": 0.692, ... },
  "insights": [
    "📊 You usually complete this task around 07:00 (55% of the time).",
    "📌 Missed 4 time(s) recently.",
    "📈 Your recent behaviour is improving — great momentum!",
    "🤖 ML model predicts 76% chance you'll complete this."
  ]
}
```
