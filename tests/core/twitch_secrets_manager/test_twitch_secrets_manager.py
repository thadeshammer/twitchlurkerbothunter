from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from server.core.twitch_secrets_manager import (
    TwitchSecretsManager,
    TwitchSecretsManagerException,
)
from server.models import SecretRead

# pylint: disable=redefined-outer-name


@pytest.fixture
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
async def test_process_token_update_from_servlet(
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


if __name__ == "__main__":
    pytest.main()
