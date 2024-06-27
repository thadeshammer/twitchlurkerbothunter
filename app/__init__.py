# app/__init__.py
import asyncio
import atexit
import logging.config
import os

from flask import Flask

from app.config import Config
from app.db import async_create_all_tables
from app.models import (
    scanning_session,
    secrets,
    stream_categories,
    stream_viewerlist_fetch,
    suspected_bot,
    twitch_user_data,
    viewer_sightings,
)
from app.routes import register_routes
from app.util import setup_logging

# Logger setup outside of create_app
setup_logging(Config.LOGGING_CONFIG_FILE)
logging.getLogger("asyncio").setLevel(
    logging.WARNING
)  #  "Using selector: EpollSelector" spam
logger = logging.getLogger("app")
logger.info("Logger is ready.")


def _at_shutdown() -> None:
    """Handle any shutdown specifics for Flask."""
    logger.info("Server is shutting down.")


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    Config.load_secrets()
    app.config.from_object(Config)
    app.debug = False

    atexit.register(_at_shutdown)

    # Log the Gunicorn worker PID
    worker_pid = os.getpid()
    logger.info(f"Gunicorn worker PID: {worker_pid}")

    with app.app_context():
        register_routes(app)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_create_all_tables())

    return app
