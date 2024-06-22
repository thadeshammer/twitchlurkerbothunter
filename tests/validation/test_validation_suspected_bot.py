from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    SuspectedBotCreate,
    SuspectedBotRead,
    SuspicionLevel,
    SuspicionReason,
)

# Mock valid response
MOCK_SUSPECTED_BOT_RESPONSE = {
    "suspected_bot_id": uuid4(),
    "twitch_account_id": 1234567890,
    "follower_count": 200,
    "following_count": 0,
    "is_banned_or_deleted": False,
    "suspicion_level": SuspicionLevel.NONE,
    "suspicion_reason": SuspicionReason.UNSPECIFIED,
    "additional_notes": "Sample notes https://somedopeurl.org I like scissors! 61.",
}


def test_suspected_bot_create_valid():
    """Test creating a SuspectedBotCreate with valid data."""
    try:
        SuspectedBotCreate(**MOCK_SUSPECTED_BOT_RESPONSE)
    except ValidationError as e:
        pytest.fail(f"Unexpected ValidationError: {e}")


def test_suspected_bot_read_valid():
    """Test creating a SuspectedBotRead with valid data."""
    try:
        SuspectedBotRead(**MOCK_SUSPECTED_BOT_RESPONSE)
    except ValidationError as e:
        pytest.fail(f"Unexpected ValidationError: {e}")


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("suspected_bot_id", "invalid_uuid", "value is not a valid uuid"),
        ("twitch_account_id", "invalid_id", "value is not a valid integer"),
        ("follower_count", -1, "ensure this value is greater than or equal to 0"),
        ("following_count", -1, "ensure this value is greater than or equal to 0"),
        (
            "is_banned_or_deleted",
            "invalid_bool",
            "value could not be parsed to a boolean",
        ),
        (
            "suspicion_level",
            "invalid_level",
            "value is not a valid enumeration member; permitted",
        ),
        (
            "suspicion_reason",
            "invalid_reason",
            "value is not a valid enumeration member; permitted",
        ),
        ("additional_notes", "無效的筆記", "string does not match regex"),
    ],
)
def test_suspected_bot_read_invalid(field, value, expected_error):
    """Test creating a SuspectedBotRead with invalid data."""
    data = MOCK_SUSPECTED_BOT_RESPONSE.copy()
    data[field] = value
    print(f">>> {field=} :: {value=} <<<")
    with pytest.raises(ValidationError) as excinfo:
        SuspectedBotRead(**data)
    print(f">>> {expected_error=} :: {excinfo.value=} <<<")
    assert expected_error in str(excinfo.value)


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("twitch_account_id", "invalid_id", "value is not a valid integer"),
        ("follower_count", -1, "ensure this value is greater than or equal to 0"),
        ("following_count", -1, "ensure this value is greater than or equal to 0"),
        (
            "is_banned_or_deleted",
            "invalid_bool",
            "value could not be parsed to a boolean",
        ),
        (
            "suspicion_level",
            "invalid_level",
            "value is not a valid enumeration member; permitted",
        ),
        (
            "suspicion_reason",
            "invalid_reason",
            "value is not a valid enumeration member; permitted",
        ),
        ("additional_notes", "無效的筆記", "string does not match regex"),
    ],
)
def test_suspected_bot_create_invalid(field, value, expected_error):
    """Test creating a SuspectedBotCreate with invalid data."""
    data = {
        "twitch_account_id": 1234567890,
        "follower_count": 200,
        "following_count": 0,
        "is_banned_or_deleted": False,
        "suspicion_level": SuspicionLevel.NONE,
        "suspicion_reason": SuspicionReason.UNSPECIFIED,
        "additional_notes": "Sample notes",
    }
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        SuspectedBotCreate(**data)
    assert expected_error in str(excinfo.value)
