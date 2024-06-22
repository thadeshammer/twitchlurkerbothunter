# test_twitch_user_data.py

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import TwitchUserDataCreate, TwitchUserDataRead

# Valid data for TwitchUserDataAPIResponse
MOCK_TWITCH_GET_USER_RESPONSE = {
    "twitch_account_id": 1234567890,
    "login_name": "validloginname",
    "display_name": "ValidDisplayName",
    "account_type": "",
    "broadcaster_type": "",
    "lifetime_view_count": 100,
    "account_created_at": datetime.now(timezone.utc),
}

# Invalid data for TwitchUserDataAPIResponse
BUSTED_TWITCH_GET_USER_RESPONSE = {
    "twitch_account_id": "invalid_id",
    "login_name": "InvalidLoginName#",
    "display_name": "InvalidDisplayName#",
    "account_type": "invalid_type",
    "broadcaster_type": "invalid_broadcaster_type",
    "lifetime_view_count": -10,
    "account_created_at": "invalid_date",
}


def test_twitch_user_data_api_response_valid():
    """Test creating a TwitchUserDataAPIResponse with valid data."""
    try:
        twitch_user_data = TwitchUserDataRead(**MOCK_TWITCH_GET_USER_RESPONSE)
        assert (
            twitch_user_data.twitch_account_id
            == MOCK_TWITCH_GET_USER_RESPONSE["twitch_account_id"]
        )
        assert (
            twitch_user_data.login_name == MOCK_TWITCH_GET_USER_RESPONSE["login_name"]
        )
        assert (
            twitch_user_data.display_name
            == MOCK_TWITCH_GET_USER_RESPONSE["display_name"]
        )
        assert (
            twitch_user_data.account_type
            == MOCK_TWITCH_GET_USER_RESPONSE["account_type"]
        )
        assert (
            twitch_user_data.broadcaster_type
            == MOCK_TWITCH_GET_USER_RESPONSE["broadcaster_type"]
        )
        assert (
            twitch_user_data.lifetime_view_count
            == MOCK_TWITCH_GET_USER_RESPONSE["lifetime_view_count"]
        )
        assert (
            twitch_user_data.account_created_at
            == MOCK_TWITCH_GET_USER_RESPONSE["account_created_at"]
        )
    except ValidationError as e:
        pytest.fail(f"Unexpected ValidationError: {e}")


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("twitch_account_id", "invalid_id", "value is not a valid integer"),
        ("login_name", "invalid_login!", "string does not match regex"),
        ("display_name", "invalid_display!", "string does not match regex"),
        ("account_type", "invalid_type", "unexpected value; permitted"),
        ("broadcaster_type", "invalid_broadcaster", "unexpected value; permitted"),
        ("lifetime_view_count", -1, "ensure this value is greater than or equal to 0"),
        ("account_created_at", "invalid_date", "invalid datetime format"),
        ("first_sighting_as_viewer", "invalid_date", "invalid datetime format"),
        ("most_recent_sighting_as_viewer", "invalid_date", "invalid datetime format"),
        (
            "most_recent_concurrent_channel_count",
            "invalid_int",
            "value is not a valid integer",
        ),
        (
            "all_time_high_concurrent_channel_count",
            "invalid_int",
            "value is not a valid integer",
        ),
        ("all_time_high_at", "invalid_date", "invalid datetime format"),
    ],
)
def test_twitch_user_data_api_response_invalid(field, value, expected_error):
    """Test creating a TwitchUserDataAPIResponse with invalid data."""
    data = {
        "twitch_account_id": 12345,
        "login_name": "validlogin",
        "display_name": "ValidDisplay",
        "account_type": "",
        "broadcaster_type": "",
        "lifetime_view_count": 100,
        "account_created_at": "2022-01-01T00:00:00Z",
        "first_sighting_as_viewer": None,
        "most_recent_sighting_as_viewer": None,
        "most_recent_concurrent_channel_count": None,
        "all_time_high_concurrent_channel_count": None,
        "all_time_high_at": None,
        "suspected_bot_id": None,
    }
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        TwitchUserDataRead(**data)
    assert expected_error in str(excinfo.value)


def test_twitch_user_data_create_valid():
    """Test creating a TwitchUserDataCreate with valid data."""
    valid_create_data = MOCK_TWITCH_GET_USER_RESPONSE.copy()
    valid_create_data.update(
        {
            "first_sighting_as_viewer": None,
            "most_recent_sighting_as_viewer": None,
            "most_recent_concurrent_channel_count": None,
            "all_time_high_concurrent_channel_count": None,
            "all_time_high_at": None,
            "suspected_bot_id": None,
        }
    )
    try:
        twitch_user_data_create = TwitchUserDataCreate(**valid_create_data)
        assert (
            twitch_user_data_create.twitch_account_id
            == valid_create_data["twitch_account_id"]
        )
        assert twitch_user_data_create.login_name == valid_create_data["login_name"]
        assert twitch_user_data_create.display_name == valid_create_data["display_name"]
        assert twitch_user_data_create.account_type == valid_create_data["account_type"]
        assert (
            twitch_user_data_create.broadcaster_type
            == valid_create_data["broadcaster_type"]
        )
        assert (
            twitch_user_data_create.lifetime_view_count
            == valid_create_data["lifetime_view_count"]
        )
        assert (
            twitch_user_data_create.account_created_at
            == valid_create_data["account_created_at"]
        )
        assert (
            twitch_user_data_create.first_sighting_as_viewer
            == valid_create_data["first_sighting_as_viewer"]
        )
        assert (
            twitch_user_data_create.most_recent_sighting_as_viewer
            == valid_create_data["most_recent_sighting_as_viewer"]
        )
        assert (
            twitch_user_data_create.most_recent_concurrent_channel_count
            == valid_create_data["most_recent_concurrent_channel_count"]
        )
        assert (
            twitch_user_data_create.all_time_high_concurrent_channel_count
            == valid_create_data["all_time_high_concurrent_channel_count"]
        )
        assert (
            twitch_user_data_create.all_time_high_at
            == valid_create_data["all_time_high_at"]
        )
    except ValidationError as e:
        pytest.fail(f"Unexpected ValidationError: {e}")


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("twitch_account_id", "invalid_id", "value is not a valid integer"),
        ("login_name", "invalid_login!", "string does not match regex"),
        ("display_name", "invalid_display!", "string does not match regex"),
        ("account_type", "invalid_type", "unexpected value; permitted"),
        ("broadcaster_type", "invalid_broadcaster", "unexpected value; permitted"),
        ("lifetime_view_count", -1, "ensure this value is greater than or equal to 0"),
        ("account_created_at", "invalid_date", "invalid datetime format"),
        ("first_sighting_as_viewer", "invalid_date", "invalid datetime format"),
        ("most_recent_sighting_as_viewer", "invalid_date", "invalid datetime format"),
        (
            "most_recent_concurrent_channel_count",
            "invalid_int",
            "value is not a valid integer",
        ),
        (
            "all_time_high_concurrent_channel_count",
            "invalid_int",
            "value is not a valid integer",
        ),
        ("all_time_high_at", "invalid_date", "invalid datetime format"),
    ],
)
def test_twitch_user_data_create_invalid(field, value, expected_error):
    """Test creating a TwitchUserDataCreate with invalid data."""
    data = MOCK_TWITCH_GET_USER_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        TwitchUserDataCreate(**data)
    assert expected_error in str(excinfo.value)