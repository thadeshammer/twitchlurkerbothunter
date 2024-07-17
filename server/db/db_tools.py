from typing import Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, inspect, select

from server.db import get_db


async def upsert_one(db_model: SQLModel, session: Optional[AsyncSession] = None):
    if session is None:
        async with get_db() as session:
            await _upsert(db_model, session)
    else:
        await _upsert(db_model, session)


async def _upsert(db_model: SQLModel, session: AsyncSession):
    # Determine what the primary key-value pair is for this item.
    model_class = db_model.__class__
    mapper = inspect(model_class)
    primary_key_column = mapper.primary_key[0].name
    primary_key_value = getattr(db_model, primary_key_column)

    # Check if the item already exists based on the primary key
    statement = select(model_class).where(
        getattr(model_class, primary_key_column) == primary_key_value
    )
    result = await session.execute(statement)
    existing_item = result.scalar_one_or_none()

    if existing_item:
        # If it exists, update the existing item
        for key, value in db_model.model_dump().items():
            setattr(existing_item, key, value)
        session.add(existing_item)
    else:
        # If it doesn't exist, insert the new item
        session.add(db_model)

    await session.commit()

    # Make sure the instance is refreshed from the session
    await session.refresh(db_model if not existing_item else existing_item)
