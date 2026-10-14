from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    return jsonify(status="ok")


# Route modules attach their views to bp on import.
from app.routes import calls, ivr  # noqa: E402,F401
