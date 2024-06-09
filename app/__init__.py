# app/__init__.py
from flask import Flask

from .config.default import Config

# from .db import get_db
from .db_base import Base, engine
from .models import observation, suspect, twitch_user_data


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Import inside the function to avoid circular import issues
        from .routes import test_routes

        # Register blueprints or routes
        app.register_blueprint(test_routes.bp)

        # Use a session to bind the metadata
        # with get_db() as db:
        Base.metadata.create_all(bind=engine)

    return app
