"""Main Flask application."""

from flask import Flask
from routes import users, health


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"

    # Register blueprints
    app.register_blueprint(users.bp)
    app.register_blueprint(health.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
