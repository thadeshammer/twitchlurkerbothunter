import logging
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# pylint: disable=unused-import
from server.models import (
    ScanningSession,
    Secret,
    StreamCategory,
    StreamViewerListFetch,
    SuspectedBot,
    TwitchUserData,
    ViewerSighting,
)
from server.models.dummy_model import DummyModel

# Set the environment to test
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="function")
def async_engine():
    # Here are a variety of things I've tried to resolve the "no such table" issue with asyncio
    # and SQLite in-memory.
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads
    # https://stackoverflow.com/questions/73485899/sqlalchemy-with-asyncpg-crashing-with-error-asyncpg-interfaceerror-cannot-per/73485900#73485900
    return create_async_engine(
        "sqlite+aiosqlite://",
        echo=True,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(async_engine) as session:
        yield session
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="module", autouse=True)
def disable_logging():
    """Automatically disable logging for all unit tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
