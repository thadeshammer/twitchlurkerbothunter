from asyncio import current_task

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+aiomysql://user:password@db/mydatabase"

# Defining these here instead of db.py addresses circular imports. Hopefully.
engine = create_async_engine(DATABASE_URL, future=True)
async_session_factory = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
AsyncSessionLocal = async_scoped_session(async_session_factory, scopefunc=current_task)


# Create a base class for all declarative models to inherit from.
Base = declarative_base()


async def async_create_all_tables():
    """Uses run_sync so the tables are created prior to anything else happening."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
