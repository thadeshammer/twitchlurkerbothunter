# app/__init__.py
from flask import Flask
from .config.default import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Import inside the function to avoid circular import issues
        from .db import get_db
        from .db_base import Base
        from .routes import test_routes

        # Use a session to bind the metadata
        with next(get_db()) as db:
            Base.metadata.create_all(bind=db.get_bind())

    return app
