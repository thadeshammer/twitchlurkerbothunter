# app/__init__.py
import logging.config
import os
from typing import Any, List, Union

import yaml
from flask import Flask

from .config.default import Config
from .db_base import Base, engine
from .models import observation, suspect, twitch_user_data
from .routes import register_routes


def setup_logging(
    default_path="logging_config.yaml", default_level=logging.DEBUG, env_key="LOG_CFG"
):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt", encoding="UTF8") as config_file:
            config: Union[List, dict, None] = yaml.safe_load(config_file.read())
        assert isinstance(config, dict)
        logging.config.dictConfig(config)
        print(f"Logging good to go: {config}", flush=True)
    else:
        print("Logging is borked, falling back on defaults.", flush=True)
        logging.basicConfig(level=default_level)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.debug = False

    setup_logging()  # should only need to call this once (here)
    logger = logging.getLogger("app")

    logger.info("Creating app")

    with app.app_context():
        logger.info("registering routes")
        register_routes(app)

        logger.info("now creating tables")
        # Use a session to bind the metadata
        Base.metadata.create_all(bind=engine)
        logger.info("done, returning app")
    return app
