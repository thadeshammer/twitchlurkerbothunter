import asyncio
import logging
import sys

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
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


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        _TEST_DB_URI, echo=True, future=True, hide_parameters=True, poolclass=NullPool
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_session_maker(async_engine):  # pylint:disable=redefined-outer-name
    return sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables(async_engine):  # pylint:disable=redefined-outer-name
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def truncate_tables(
    async_engine,
):  # pylint:disable=redefined-outer-name  # type: ignore
    async with async_engine.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name};"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await conn.commit()
    yield


@pytest_asyncio.fixture(scope="function")
async def async_session(
    async_session_maker, truncate_tables  # type: ignore
):  # pylint:disable=redefined-outer-name
    async with async_session_maker() as session:
        yield session
        await session.close()


@pytest.fixture(scope="module", autouse=True)
def disable_logging():
    """Automatically disable logging for all unit tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
