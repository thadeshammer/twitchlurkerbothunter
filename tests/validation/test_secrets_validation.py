from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from server.models.secrets import Secret, SecretCreate, SecretRead

VALID_SECRET_DATA = {
    "access_token": "validAccessToken123456",
    "refresh_token": "validRefreshToken123456",
    "expires_in": 3600,
    "token_type": "bearer",
    "scope": "user:read:email",
}


def test_secret_create_valid():
    secret = SecretCreate(**VALID_SECRET_DATA)
    assert secret.access_token == VALID_SECRET_DATA["access_token"]
    assert secret.refresh_token == VALID_SECRET_DATA["refresh_token"]
    assert secret.expires_in == VALID_SECRET_DATA["expires_in"]
    assert secret.token_type == VALID_SECRET_DATA["token_type"]
    assert secret.scope == VALID_SECRET_DATA["scope"]


@pytest.mark.parametrize(
    "key, value",
    [
        ("access_token", ""),
        ("access_token", "invalid_token"),
        ("refresh_token", ""),
        ("refresh_token", "invalid_token"),
        ("expires_in", 0),
        ("expires_in", -100),
        ("token_type", ""),
        ("scope", ""),
    ],
)
def test_secret_create_invalid(key, value):
    invalid_data = VALID_SECRET_DATA.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        SecretCreate(**invalid_data)


def test_secret_read():
    secret_data = VALID_SECRET_DATA.copy()
    secret_data["id"] = 1
    secret_data["last_update_timestamp"] = datetime.now(timezone.utc)

    secret = SecretRead(**secret_data)
    assert secret.id == secret_data["id"]
    assert secret.access_token == secret_data["access_token"]
    assert secret.refresh_token == secret_data["refresh_token"]
    assert secret.expires_in == secret_data["expires_in"]
    assert secret.token_type == secret_data["token_type"]
    assert secret.scope == secret_data["scope"]
    assert secret.last_update_timestamp == secret_data["last_update_timestamp"]


def test_secret_last_update_timestamp_default():
    secret_data = VALID_SECRET_DATA.copy()
    secret_data["id"] = 1

    secret = Secret(**secret_data)
    assert isinstance(secret.last_update_timestamp, datetime)
    assert secret.last_update_timestamp <= datetime.now(timezone.utc)
