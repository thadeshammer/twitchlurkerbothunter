import logging

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from server.config import Config

# pylint: disable=unused-import
from server.models import (
    ScanningSession,
    StreamCategory,
    StreamViewerListFetch,
    SuspectedBot,
    TwitchUserData,
    ViewerSighting,
)
from server.models.dummy_model import DummyModel

_TEST_DB_URI = Config.get_db_uri()


@pytest.fixture(scope="function")
def async_engine():
    return create_async_engine(_TEST_DB_URI, echo=True, future=True, hide_parameters=True)


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):  # pylint:disable=redefined-outer-name
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
