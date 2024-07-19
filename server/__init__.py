# server/__init__.py
import logging
import os
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from server.config import Config
from server.db import async_create_all_tables

# Import tables for creation here.
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
from server.utils import setup_logging

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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to debug level to capture detailed logs
logger.info("Logger is ready.")


@asynccontextmanager
async def lifespan(
    fastapi_app: FastAPI,  # type: ignore  pylint:disable=unused-argument
) -> AsyncGenerator[None, None]:
    # Startup event
    await async_create_all_tables()

    yield  # this allows the server to run

    # Shutdown event
    # Add any necessary cleanup code here


def create_app() -> FastAPI:
    fastapi_app = FastAPI(lifespan=lifespan)

    Config.initialize()
    fastapi_app.debug = False

    logger.info("Logger is ready.")

    # Log the worker PID
    worker_pid = os.getpid()
    logger.info(f"Worker PID: {worker_pid}")

    fastapi_app.include_router(router)

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=CERT_FILE_PATH,
        keyfile=KEY_FILE_PATH,
        password=CERT_PASSKEY,
    )
