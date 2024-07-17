# server/core/twitch_secrets_manager.py
"""
    SecretsManager

    This module will handle the tokens.

    - When the servlet sends us fresh tokens, we update and blow away the olds ones.
    - When the token expires, this module will try to refresh it with the refresh token. If refresh
      fails we no longer have tokens.
    - If we don't have tokens (because the row is empty or expired) then we're dead in the water and
      we respond that we can't act. (Some other part of the app should poke the user to fix this.)
"""
import asyncio
import logging
from datetime import datetime, timezone
from multiprocessing import Lock as multi_proc_lock
from multiprocessing import Manager as multi_proc_manager
from typing import Any, Optional

from pydantic import ValidationError
from sqlmodel import select

from server.db import get_db, upsert_one
from server.models import Secret, SecretCreate

logger = logging.getLogger("server")


class TwitchSecretsManagerException(Exception):
    pass


class TwitchSecretsManager:
    _singleton_instance: Optional["TwitchSecretsManager"] = None
    _manager = multi_proc_manager()

    def __new__(cls):
        if cls._singleton_instance is None:
            cls._singleton_instance = super(TwitchSecretsManager, cls).__new__(cls)
        return cls._singleton_instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # To prevent reinitialization
            self._secrets_store: Optional[Secret] = None
            self._process_lock: multi_proc_lock = self._manager.Lock()
            self._async_lock = asyncio.Lock()
            self.initialized = True

    async def _insert_or_update_secret(self, new_secret: SecretCreate):
        secret = Secret(**new_secret.model_dump())
        self._secrets_store = secret.model_copy()

        try:
            async with get_db() as session:
                await upsert_one(secret, session)
        except Exception as e:
            self._secrets_store = None  # invalidated
            raise TwitchSecretsManagerException("Couldn't store secret.") from e

        if self._secrets_store is not None:
            logger.debug(
                f"{self._secrets_store.expires_in} {self._secrets_store.last_update_timestamp}"
            )
        else:
            logger.debug("The secrets_store is empty and we are very sad now.")

    async def process_token_update_from_servlet(
        self, servlet_payload: dict[str, Any]
    ) -> bool:

        try:
            new_secret = SecretCreate(**servlet_payload)
            new_secret.last_update_timestamp = datetime.now(timezone.utc)
        except ValidationError as e:
            logger.error(f"SecretCreate validation failed: {e.errors()}")
            raise TwitchSecretsManagerException from e

        logger.info(f"Tokens received: {new_secret.expires_in=}, {new_secret.scope=}")

        try:
            await self._insert_or_update_secret(new_secret)
        except Exception as e:
            logger.error(f"Failed to insert or update secret: {str(e)}")
            raise TwitchSecretsManagerException from e

        return True

    async def get_access_token(self) -> Optional[str]:
        # if _secrets_store is None, attempt to fetch from DB
        if self._secrets_store is None:
            async with get_db() as session:
                result = await session.execute(select(Secret))
                self._secrets_store = result.scalar_one_or_none()

        # if _secrets_store.access_token is expired, attempt to refresh

        # if cannot refresh and/or has no token, throw an error
        if self._secrets_store is None:
            raise TwitchSecretsManagerException("No token. Use oauth servlet.")

        if self._secrets_store is not None:
            return self._secrets_store.access_token

        return None
