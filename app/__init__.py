# app/__init__.py
import asyncio
import logging
import os

from flask import Flask

from app.config import Config
from app.db import async_create_all_tables
from app.models import (
    ScanningSession,
    Secret,
    StreamCategory,
    StreamViewerListFetch,
    SuspectedBot,
    TwitchUserData,
    ViewerSighting,
)
from app.routes import register_routes


async def create_app() -> Flask:
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
        await async_create_all_tables()

    return app
