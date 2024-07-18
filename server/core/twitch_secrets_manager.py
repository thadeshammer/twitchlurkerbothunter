# server/core/twitch_secrets_manager.py
"""
    SecretsManager

    This module will handle the tokens.

    - When the servlet sends us fresh tokens, we update and blow away the olds ones.
    - When the token expires, this module will try to refresh it with the refresh token. If refresh
      fails we no longer have tokens.
    - If we don't have tokens (because the row is empty or expired) then we're dead in the water and
      we respond that we can't act. (Some other part of the app should poke the user to fix this.)

    CONCURRENCY NOTES

    This module is rigged up to be hammered by each worker directly and is a singleton. It leverages
    locking mechanisms to ensure this is the case.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from multiprocessing import Lock as multi_proc_lock
from multiprocessing import Manager as multi_proc_manager
from typing import Any, Optional

from pydantic import ValidationError

from server.db import get_db, upsert_one
from server.db.query import fetch_secret
from server.models import Secret, SecretCreate

logger = logging.getLogger("server")


class TwitchSecretsManagerException(Exception):
    pass


class TwitchSecretsManager:
    _singleton_instance: Optional["TwitchSecretsManager"] = None
    _manager = multi_proc_manager()
    _singleton_lock = _manager.Lock()

    def __new__(cls):
        with cls._singleton_lock:
            if cls._singleton_instance is None:
                cls._singleton_instance = super(TwitchSecretsManager, cls).__new__(cls)
        return cls._singleton_instance

    def __init__(self):
        with self._singleton_lock:
            if not hasattr(self, "initialized"):  # To prevent reinitialization
                self._secrets_store: Optional[Secret] = None
                self._process_lock: multi_proc_lock = self._manager.Lock()
                self._async_lock = asyncio.Lock()
                self.expiration_time: Optional[datetime] = None
                self.initialized = True

    @staticmethod
    def _calculate_expiry_time(lifetime_in_seconds: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=lifetime_in_seconds)

    async def _insert_or_update_secret(self, new_secret: SecretCreate):
        """DO NOT CALL DIRECTLY. CALL process_token_update_from_servlet OR IT WILL BE BAD.

        Performs upsert op for a new Secret and updates the singleton's store.

        Args:
            new_secret (SecretCreate): The validated SecretCreate SQLModel.

        Raises:
            TwitchSecretsManagerException: In the event of a DB error we can't recover from.
        """
        secret = Secret(**new_secret.model_dump())
        self._secrets_store = secret.model_copy()
        self.expiration_time = self._calculate_expiry_time(secret.expires_in)

        try:
            async with get_db() as session:
                await upsert_one(secret, session)
        except Exception as e:
            self._secrets_store = None  # invalidated
            self.expiration_time = None  # invalidated
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
        """Call this from the store-token route with new tokens + metadata

        Args:
            servlet_payload (dict[str, Any]): The payload from the Twitch oauth servlet.

        Raises:
            TwitchSecretsManagerException: Validation faiure.
            TwitchSecretsManagerException: DB upsert failure.

        Returns:
            bool: True if update succeeded; False otherwise.
        """
        with self._process_lock:
            async with self._async_lock:
                try:
                    new_secret = SecretCreate(**servlet_payload)
                    new_secret.last_update_timestamp = datetime.now(timezone.utc)
                except ValidationError as e:
                    logger.error(f"SecretCreate validation failed: {e.errors()}")
                    raise TwitchSecretsManagerException from e

                logger.info(
                    f"Tokens received: {new_secret.expires_in=}, {new_secret.scope=}"
                )
                token_portion = new_secret.access_token[:5]
                logger.debug(f"Token: {token_portion}")

                try:
                    await self._insert_or_update_secret(new_secret)
                except Exception as e:
                    logger.error(f"Failed to insert or update secret: {str(e)}")
                    raise TwitchSecretsManagerException from e

                return True

    async def _refresh_tokens(self):
        pass

    async def get_access_token(self) -> Optional[str]:
        with self._process_lock:
            async with self._async_lock:
                # if _secrets_store is None, attempt to fetch from DB
                if self._secrets_store is None:
                    self._secrets_store = await fetch_secret()

                if self._secrets_store:
                    token_portion = self._secrets_store.access_token[:5]
                    logger.debug(f"Token loaded: {token_portion}")
                    self.expiration_time = self._calculate_expiry_time(
                        self._secrets_store.expires_in
                    )

                # if _secrets_store.access_token is expired, attempt to refresh
                if self._secrets_store and self.expiration_time:
                    if datetime.now(timezone.utc) >= self.expiration_time:
                        await self._refresh_tokens()

                # if cannot refresh and/or has no token, throw an error
                if self._secrets_store is None:
                    raise TwitchSecretsManagerException("No token. Use oauth servlet.")

                if self._secrets_store is not None:
                    return self._secrets_store.access_token

                return None
