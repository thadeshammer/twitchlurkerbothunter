from unittest.mock import patch

import pytest
from sqlmodel import select

from server.core.twitch_secrets_manager import (
    TwitchSecretsManager,
    TwitchSecretsManagerException,
)
from server.models import Secret, SecretRead


@pytest.mark.asyncio
async def test_get_access_token_no_secrets():
    secrets_manager = TwitchSecretsManager()
    with pytest.raises(
        TwitchSecretsManagerException, match="No token. Use oauth servlet."
    ):
        await secrets_manager.get_access_token()


@pytest.mark.asyncio
@patch("server.db.db.get_db")
async def test_get_access_token_secret(mock_get_db, async_session):
    mock_get_db.return_value = async_session

    # Set up
    first_secret_payload = {
        "access_token": "accessToken",
        "refresh_token": "refreshToken",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": "chat:read",
        "enforce_one_row": "enforce_one_row",
    }

    secrets_manager = TwitchSecretsManager()
    await secrets_manager.process_token_update_from_servlet(first_secret_payload)

    await async_session.commit()  # hand testing edgecase of rapid query chaser

    token = await secrets_manager.get_access_token()
    assert token == first_secret_payload["access_token"]

    await async_session.close()


@pytest.mark.asyncio
@patch("server.db.db.get_db")
async def test_process_token_update_from_servlet(mock_get_db, async_session):
    mock_get_db.return_value = async_session
    secrets_manager = TwitchSecretsManager()

    # Set up
    first_secret_payload = {
        "access_token": "1stAccessToken",
        "refresh_token": "1stRefreshToken",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": "chat:read",
        "enforce_one_row": "enforce_one_row",
    }

    await secrets_manager.process_token_update_from_servlet(first_secret_payload)

    result1 = await async_session.execute(select(Secret))
    secret1: SecretRead = result1.scalar_one_or_none()

    assert secret1.access_token == first_secret_payload["access_token"]

    # Replace it
    second_secret_payload = {
        "access_token": "2ndAccessToken",
        "refresh_token": "2ndRefreshToken",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": "chat:read",
        "enforce_one_row": "enforce_one_row",
    }

    await secrets_manager.process_token_update_from_servlet(second_secret_payload)

    await async_session.commit()  # Need to commit and close out transaction for refresh to work
    await async_session.refresh(
        secret1
    )  # Weird edge case because of back-to-back select(Secret)

    result2 = await async_session.execute(select(Secret))
    secret2: SecretRead = result2.scalar_one_or_none()

    assert secret2.access_token == second_secret_payload["access_token"]

    await async_session.close()
