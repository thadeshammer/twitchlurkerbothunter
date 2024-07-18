# server/db/query.py
"""Centralized location for app queries to seperate the ORM from the core.
"""
from typing import Optional

from sqlmodel import select

from server.models import Secret, SecretRead

from .db import get_db


async def fetch_secret() -> Optional[Secret]:
    """There's only ever one secret in the table.

    SecretRead includes only the row id in addition to the rest of the data, which is only used in
    debugging, so we convert to proper Secret.

    Returns:
        Optional[Secret]: The singular row from the Secrets table or None.
    """
    async with get_db() as session:
        result = await session.execute(select(Secret))
    secret_read: SecretRead = result.scalar_one_or_none()
    return Secret(**secret_read.model_dump())
