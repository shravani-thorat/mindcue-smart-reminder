"""
Recommendation routes — including ML model explanation endpoint.
"""

from flask import Blueprint, jsonify
from services.recommendation_service import get_all_recommendations, get_recommendation_for_task
from services.ml_model import predict_completion_probability
from services.task_service import get_task_by_id

rec_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")

def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code
def _ok(data):            return jsonify({"success": True,  "data": data})


@rec_bp.route("", methods=["GET"])
def all_recommendations():
    return _ok(get_all_recommendations())


@rec_bp.route("/<int:task_id>", methods=["GET"])
def task_recommendation(task_id):
    task = get_task_by_id(task_id)
    if not task: return _err("Task not found.", 404)
    return _ok(get_recommendation_for_task(task))


@rec_bp.route("/<int:task_id>/ml", methods=["GET"])
def ml_detail(task_id):
    """Returns the raw ML model output including feature vector."""
    if not get_task_by_id(task_id): return _err("Task not found.", 404)
    return _ok(predict_completion_probability(task_id))
