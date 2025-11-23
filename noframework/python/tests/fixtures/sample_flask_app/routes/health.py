"""Health check routes."""

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health_check():
    """Return application health status."""
    return jsonify({"status": "healthy"})
