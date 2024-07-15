from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db import get_db, upsert_one
from server.models.dummy_model import DummyModel


@pytest.mark.asyncio
async def test_upsert_insert(async_session):
    # Arrange
    dummy_model = DummyModel(id=1, name="Test", value=100)

    # Act
    await upsert_one(dummy_model, session=async_session)

    # Assert
    result = await async_session.execute(select(DummyModel).where(DummyModel.id == 1))
    retrieved = result.scalar_one()
    assert retrieved.name == "Test"
    assert retrieved.value == 100


@pytest.mark.asyncio
async def test_upsert_update(async_session):
    # Arrange
    dummy_model = DummyModel(id=1, name="Test", value=100)
    await upsert_one(dummy_model, session=async_session)

    updated_dummy_model = DummyModel(id=1, name="Test Updated", value=200)

    # Act
    await upsert_one(updated_dummy_model, session=async_session)

    # Assert
    result = await async_session.execute(select(DummyModel).where(DummyModel.id == 1))
    retrieved = result.scalar_one()
    assert retrieved.name == "Test Updated"
    assert retrieved.value == 200
