# app/__init__.py
import logging.config
import os
from typing import List, Union

import yaml
from flask import Flask

from app.config import Config
from app.db import Base, engine
from app.models import observation, suspect, twitch_user_data
from app.routes import register_routes
from app.util import setup_logging


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    Config.load_secrets()
    app.config.from_object(Config)
    app.debug = False

    setup_logging(Config.LOGGING_CONFIG_FILE)
    logger = logging.getLogger("app")
    logger.info("Logger is ready.")

    with app.app_context():
        register_routes(app)
        Base.metadata.create_all(bind=engine)
    return app
