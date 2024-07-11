# app/__init__.py
import asyncio
import logging
import os
import ssl

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from server.config import Config
from server.db import async_create_all_tables
from server.models import (
    ScanningSession,
    Secret,
    StreamCategory,
    StreamViewerListFetch,
    SuspectedBot,
    TwitchUserData,
    ViewerSighting,
)
from server.routes import router
from server.util import setup_logging

CERT_FILE_PATH = "/secrets/cert.pem"
KEY_FILE_PATH = "/secrets/key.pem"

CERT_PASSKEY = str(os.getenv("CERT_PASSKEY"))
if not CERT_PASSKEY:
    raise EnvironmentError("CERT_PASSKEY environment variable not set")

# Logger setup outside of create_app
setup_logging(Config.LOGGING_CONFIG_FILE)
logging.getLogger("asyncio").setLevel(
    logging.WARNING
)  # "Using selector: EpollSelector" spam
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)  # Set to debug level to capture detailed logs
logger.info("Logger is ready.")


def create_app() -> FastAPI:
    fastapi_app = FastAPI()

    Config.load_secrets()
    fastapi_app.debug = False

    logger.info("Logger is ready.")

    # Log the worker PID
    worker_pid = os.getpid()
    logger.info(f"Worker PID: {worker_pid}")

    fastapi_app.include_router(router)

    @fastapi_app.on_event("startup")
    async def on_startup():
        await async_create_all_tables()

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=CERT_FILE_PATH,
        keyfile=KEY_FILE_PATH,
        password=CERT_PASSKEY,
    )
