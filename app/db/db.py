from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

DATABASE_URL = "mysql+aiomysql://user:password@db/mydatabase"

# Creating async engine
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as async_session:
        yield async_session


# async def async_create_all_tables():
#     async with async_engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.create_all)
