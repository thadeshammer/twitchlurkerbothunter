# app/db.py
"""
    SQLAlchemy DB Session Helper Functions

    Sample:

    # Assuming you have a model defined, for example:
    # from your models import YourModel

        async def async_main():
            # Write transaction
            async with get_db() as db:
                new_record = YourModel(field1="value1", field2="value2")
                db.add(new_record)
                await db.commit()

            # Read transaction
            async with get_db() as db:
                result = await db.execute(select(YourModel).filter_by(field1="value1"))
                record = result.scalars().first()
                print(record)

        if __name__ == "__main__":
            asyncio.run(async_main())
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from flask import current_app
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ConfigKey
from app.exceptions import DatabaseConnectionError

from .base import AsyncSessionLocal


async def _get_session() -> AsyncSession:
    retries = 0
    max_retries = current_app.config[ConfigKey.SQLALCHEMY_CONNECT_MAX_RETRIES]
    retry_interval = current_app.config[ConfigKey.SQLALCHEMY_CONNECT_RETRY_INTERVAL]

    db: Optional[AsyncSession] = None
    while retries < max_retries and db is None:
        try:

            db = AsyncSessionLocal()

        except OperationalError as e:
            retries += 1
            await asyncio.sleep(retry_interval)
            if retries >= max_retries:
                raise DatabaseConnectionError(
                    "Failed to connect to the database after multiple retries."
                ) from e

    assert db is not None  # It it were, we'd have raised an exception already.
    return db


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = await _get_session()
    try:
        yield db
    finally:
        await db.close()
        await AsyncSessionLocal.remove()
