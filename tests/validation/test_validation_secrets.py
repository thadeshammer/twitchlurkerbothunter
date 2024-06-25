# tests/validation/test_validation_secrets.py
import pytest
from pydantic import ValidationError

from app.models.secrets import SecretCreate

MOCK_ACCESS_TOKEN = "abCDeFgHiJkLmNoPqRsTuVwXyZaBcDeFgHiJkLmNoPqRsTuVwXy"
MOCK_REFRESH_TOKEN = "1234567890abcdef1234567890abcdef1234567890abcdef12"

MOCK_TWITCH_API_RESPONSE = {
    "access_token": MOCK_ACCESS_TOKEN,
    "refresh_token": MOCK_REFRESH_TOKEN,
    "expires_in": "3600",
    "token_type": "bearer",
    "scope": "chat:read",
}


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("expires_in", "-1", "ensure this value is greater than 0"),
        (
            "token_type",
            "",
            "value is not a valid enumeration member; permitted: 'bearer'",
        ),
    ],
)
def test_secret_create_invalid(field: str, value: str, expected_error: str):
    """Test creating a SecretCreate with invalid data."""
    data: dict[str, str] = MOCK_TWITCH_API_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        SecretCreate(**data)
    assert expected_error in str(excinfo.value)


def test_secret_create_valid():
    """Test creating a SecretCreate with valid data."""
    data = MOCK_TWITCH_API_RESPONSE.copy()

    instance = SecretCreate(**data)
    assert instance.access_token == MOCK_ACCESS_TOKEN
    assert instance.refresh_token == MOCK_REFRESH_TOKEN
    assert instance.expires_in == 3600
    assert instance.token_type == "bearer"
    assert instance.scope == "chat:read"
