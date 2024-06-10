# app/__init__.py
import os
from typing import Any, List, Union

import yaml
from flask import Flask
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from .config.default import Config
from .db_base import Base, engine
from .models import observation, suspect, twitch_user_data
from .routes import register_routes


class HandlerConfig(BaseModel):
    sink: str
    level: str
    format: str
    rotation: str = Field(None)
    retention: str = Field(None)
    compression: str = Field(None)


class LoggingConfig(BaseModel):
    handlers: List[HandlerConfig]


def setup_logging():
    with open("logging_config.yaml", "r", encoding="UTF8") as file:
        config_dict: Union[dict, List, None] = yaml.safe_load(file.read())

    try:
        # We're using Pydantic to validate what comes in from the config file that I made
        # because we all want Pylance to feel loved.
        config = LoggingConfig(**config_dict)  # type: ignore
    except ValidationError as e:
        logger.error(f"Error parsing logging configuration: {e}")
        return

    # Ensure log directory exists
    log_directory = "/logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    handlers = [handler.dict() for handler in config.handlers]
    logger.configure(handlers=handlers)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.debug = True

    setup_logging()
    logger.info("Creating app")

    with app.app_context():
        logger.info("registering routes")
        register_routes(app)

        logger.info("now creating tables")
        # Use a session to bind the metadata
        Base.metadata.create_all(bind=engine)
        logger.info("done, returning app")
    return app
