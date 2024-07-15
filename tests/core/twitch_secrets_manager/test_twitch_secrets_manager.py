from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlmodel import select

from server.core.twitch_secrets_manager import (
    TwitchSecretsManager,
    TwitchSecretsManagerException,
)
from server.models import Secret, SecretRead

# pylint: disable=redefined-outer-name


@pytest_asyncio.fixture
def secrets_manager():
    return TwitchSecretsManager()


@pytest.mark.asyncio
@patch(
    "server.core.twitch_secrets_manager.TwitchSecretsManager._get_secret_row",
    new_callable=AsyncMock,
)
async def test_get_access_token_no_secrets(mock_get_secret_row, secrets_manager):
    mock_get_secret_row.side_effect = Exception("No secret found")

    with pytest.raises(
        TwitchSecretsManagerException, match="No token. Please auth with servlet."
    ):
        await secrets_manager.get_access_token()


@pytest.mark.asyncio
@patch(
    "server.core.twitch_secrets_manager.TwitchSecretsManager._get_secret_row",
    new_callable=AsyncMock,
)
async def test_get_access_token_with_secrets(mock_get_secret_row, secrets_manager):
    fake_secret = SecretRead(
        access_token="testAccessToken",
        refresh_token="testRefreshToken",
        expires_in=3600,
        token_type="bearer",
        scope="test_scope",
        id=1,
        last_update_timestamp=datetime.now(),
    )
    mock_get_secret_row.return_value = fake_secret

    token = await secrets_manager.get_access_token()
    assert token == "testAccessToken"


@pytest.mark.asyncio
@patch(
    "server.core.twitch_secrets_manager.TwitchSecretsManager._insert_or_update_secret",
    new_callable=AsyncMock,
)
async def test_process_token_insert_from_servlet(
    mock_insert_or_update_secret, secrets_manager
):
    new_secret_payload = {
        "access_token": "newAccessToken",
        "refresh_token": "newRefreshToken",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": "test_scope",
        "enforce_one_row": "enforce_one_row",
    }

    result = await secrets_manager.process_token_update_from_servlet(new_secret_payload)
    assert result is True
    mock_insert_or_update_secret.assert_called_once()


@pytest.mark.asyncio
async def test_process_token_update_from_servlet(async_engine):
    first_secret_payload = {
        "access_token": "oldAccessToken",
        "refresh_token": "oldRefreshToken",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": "test_scope",
        "enforce_one_row": "enforce_one_row",
    }

    second_secret_payload = {
        "access_token": "newAccessToken",
        "refresh_token": "newRefreshToken",
        "expires_in": 4600,
        "token_type": "bearer",
        "scope": "test_scope",
        "enforce_one_row": "enforce_one_row",
    }

    secrets_manager = TwitchSecretsManager()

    result1 = await secrets_manager.process_token_update_from_servlet(
        first_secret_payload
    )
    assert result1 is True

    # statement = select(Secret).where(Secret.enforce_one_row == "enforce_one_row")
    # query_result = await async_engine.execute(statement)
    # existing_secret: SecretRead = query_result.scalar_one_or_none()

    # assert existing_secret.access_token == first_secret_payload["access_token"]
    # assert secrets_manager.get_access_token() == first_secret_payload["access_token"]

    # result2 = await secrets_manager.process_token_update_from_servlet(
    #     second_secret_payload
    # )
    # assert result2 is True

    # statement = select(Secret).where(Secret.enforce_one_row == "enforce_one_row")
    # query_result = await async_engine.execute(statement)
    # current_secret: SecretRead = query_result.scalar_one_or_none()

    # assert current_secret.access_token == second_secret_payload["access_token"]
    # assert secrets_manager.get_access_token() == second_secret_payload["access_token"]
