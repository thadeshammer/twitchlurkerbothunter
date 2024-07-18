# server/db/query.py
"""Centralized location for app queries to seperate the ORM from the core.
"""
from typing import Optional

from sqlmodel import select

from server.models import Secret

from .db import get_db


async def fetch_secrets_table() -> Optional[Secret]:
    async with get_db() as session:
        result = await session.execute(select(Secret))
    secret_read = result.scalar_one_or_none()
    return Secret(**secret_read.model_dump())
