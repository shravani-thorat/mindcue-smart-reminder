"""
Task routes: CRUD + mark-complete + history endpoints.
"""

from flask import Blueprint, request, jsonify
from services.task_service import (
    create_task, get_all_tasks, get_task_by_id,
    update_task, delete_task, mark_task_complete,
    log_missed_task, get_task_history,
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def _err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code


def _ok(data, code=200):
    return jsonify({"success": True, "data": data}), code


# ── POST /api/tasks ───────────────────────────────────────────────────────────
@tasks_bp.route("", methods=["POST"])
def add_task():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    scheduled_time = (body.get("scheduled_time") or "").strip()
    if not title:
        return _err("'title' is required.")
    if not scheduled_time:
        return _err("'scheduled_time' is required (HH:MM).")
    task = create_task(
        title=title,
        scheduled_time=scheduled_time,
        frequency=body.get("frequency", "daily"),
        description=body.get("description"),
        priority=int(body.get("priority", 1)),
    )
    return _ok(task, 201)


# ── GET /api/tasks ────────────────────────────────────────────────────────────
@tasks_bp.route("", methods=["GET"])
def list_tasks():
    return _ok(get_all_tasks())


# ── GET /api/tasks/<id> ───────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return _err("Task not found.", 404)
    return _ok(task)


# ── PUT /api/tasks/<id> ───────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
def edit_task(task_id):
    if not get_task_by_id(task_id):
        return _err("Task not found.", 404)
    body = request.get_json(silent=True) or {}
    task = update_task(task_id, **body)
    return _ok(task)


# ── DELETE /api/tasks/<id> ────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
def remove_task(task_id):
    if not get_task_by_id(task_id):
        return _err("Task not found.", 404)
    delete_task(task_id)
    return _ok({"deleted_id": task_id})


# ── POST /api/tasks/<id>/complete ─────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    body = request.get_json(silent=True) or {}
    result, error = mark_task_complete(task_id, notes=body.get("notes"))
    if error:
        return _err(error, 404)
    return _ok(result)


# ── POST /api/tasks/<id>/missed ───────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>/missed", methods=["POST"])
def missed_task(task_id):
    if not get_task_by_id(task_id):
        return _err("Task not found.", 404)
    log_missed_task(task_id)
    return _ok({"message": "Missed event logged, priority updated."})


# ── GET /api/tasks/<id>/history ───────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>/history", methods=["GET"])
def task_history(task_id):
    if not get_task_by_id(task_id):
        return _err("Task not found.", 404)
    return _ok(get_task_history(task_id))
