import os
from flask import Flask, send_from_directory
from database.db import init_db
from routes.task_routes import tasks_bp
from routes.recommendation_routes import rec_bp

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_SORT_KEYS"] = False

# Register blueprints
app.register_blueprint(tasks_bp)
app.register_blueprint(rec_bp)


# Serve frontend
@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/health")
def health():
    return {"status": "ok", "app": "Smart Reminder Engine"}


# Global error handlers
@app.errorhandler(404)
def not_found(e):
    return {"success": False, "error": "Resource not found."}, 404


@app.errorhandler(500)
def server_error(e):
    return {"success": False, "error": "Internal server error."}, 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
