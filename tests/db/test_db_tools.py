import pytest
from sqlmodel import select

from server.db import upsert_one
from server.models.sqlmodel.dummy_model import DummyModel


@pytest.mark.asyncio
async def test_upsert_insert(async_session):
    """Test one upsert which winds up being a create/insert call."""
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
    """Test two upserts so the second one is an update call."""
    dummy_model = DummyModel(id=1, name="Test", value=100)
    await upsert_one(dummy_model, session=async_session)

    result = await async_session.execute(select(DummyModel).where(DummyModel.id == 1))
    retrieved = result.scalar_one()
    assert retrieved.name == "Test"
    assert retrieved.value == 100

    updated_dummy_model = DummyModel(id=1, name="Test Updated", value=200)
    await upsert_one(updated_dummy_model, session=async_session)

    result = await async_session.execute(select(DummyModel).where(DummyModel.id == 1))
    retrieved = result.scalar_one()
    assert retrieved.name == "Test Updated"
    assert retrieved.value == 200
