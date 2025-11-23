"""User management routes."""

from flask import Blueprint, jsonify, request

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.route("/", methods=["GET"])
def list_users():
    """List all users."""
    return jsonify({"users": []})


@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get a specific user by ID."""
    return jsonify({"id": user_id, "name": "Test User"})


@bp.route("/", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json()
    return jsonify({"id": 1, "name": data.get("name")}), 201
