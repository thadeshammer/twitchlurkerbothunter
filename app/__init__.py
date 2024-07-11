# app/__init__.py
import asyncio
import logging
import os

from flask import Flask

from app.config import Config

# from app.db import async_create_all_tables
from app.models import (
    scanning_session,
    secrets,
    stream_categories,
    stream_viewerlist_fetch,
    suspected_bot,
    twitch_user_data,
    viewer_sighting,
)
from app.routes import register_routes


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    Config.load_secrets()
    app.config.from_object(Config)
    app.debug = False

    logger = logging.getLogger("app")
    logger.info("Logger is ready.")

    # Log the Gunicorn worker PID
    worker_pid = os.getpid()
    logger.info(f"Worker PID: {worker_pid}")

    with app.app_context():
        register_routes(app)

        # TODO fix the db <_<
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(async_create_all_tables())

    return app
