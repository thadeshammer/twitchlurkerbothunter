from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.twitch_user_data import (
    TwitchUserDataAPIResponse,
    TwitchUserDataAppData,
    TwitchUserDataCreate,
    TwitchUserDataFromGetStreamAPIResponse,
    TwitchUserDataRead,
    merge_twitch_user_data,
)

MOCK_TWITCH_API_RESPONSE = {
    "id": "123456",
    "login": "example_user",
    "type": "",
    "broadcaster_type": "",
    "view_count": "1000",
    "created_at": "2013-06-03T19:12:02Z",
}

MOCK_APP_DATA = {
    "first_sighting_as_viewer": datetime.now(timezone.utc),
    "most_recent_sighting_as_viewer": datetime.now(timezone.utc),
    "most_recent_concurrent_channel_count": 100,
    "all_time_high_concurrent_channel_count": 100,
    "all_time_high_at": datetime.now(timezone.utc),
}


def test_twitch_user_data_create_valid():
    """Test creating a TwitchUserDataCreate with valid data."""
    api_data = TwitchUserDataAPIResponse(**MOCK_TWITCH_API_RESPONSE)
    app_data = TwitchUserDataAppData(**MOCK_APP_DATA)
    combined_data = merge_twitch_user_data(api_data, app_data)
    assert combined_data.twitch_account_id == 123456
    assert combined_data.login_name == "example_user"
    assert combined_data.account_type == ""
    assert combined_data.broadcaster_type == ""
    assert combined_data.lifetime_view_count == 1000
    assert combined_data.account_created_at == datetime.fromisoformat(
        "2013-06-03T19:12:02+00:00"
    )


def test_twitch_user_data_read_valid():
    """Test creating a TwitchUserDataRead with valid data."""
    api_data = TwitchUserDataAPIResponse(**MOCK_TWITCH_API_RESPONSE)
    app_data = TwitchUserDataAppData(**MOCK_APP_DATA)

    data: TwitchUserDataCreate = merge_twitch_user_data(api_data, app_data)

    instance = TwitchUserDataRead(**data.dict())
    assert instance.twitch_account_id == 123456
    assert instance.login_name == "example_user"
    assert instance.account_type == ""
    assert instance.broadcaster_type == ""
    assert instance.lifetime_view_count == 1000
    assert instance.account_created_at == datetime.fromisoformat(
        "2013-06-03T19:12:02+00:00"
    )


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("id", "invalid_id", "invalid literal for int() with base 10: 'invalid_id'"),
        ("login", "invalid_login!", "string does not match regex"),
        ("type", "invalid_type", "unexpected value; permitted"),
        ("broadcaster_type", "invalid_broadcaster", "unexpected value; permitted"),
        ("view_count", -1, "ensure this value is greater than or equal to 0"),
        (
            "created_at",
            "invalid_date",
            "Invalid isoformat string: 'invalid_date' (type=value_error)",
        ),
    ],
)
def test_twitch_user_data_helix_api_data_invalid(
    field: str, value: str, expected_error: str
) -> None:
    """Test creating a TwitchUserDataHelixAPIData with invalid data."""
    data: dict[str, str] = MOCK_TWITCH_API_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        TwitchUserDataAPIResponse(**data)
    assert expected_error in str(excinfo.value)


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        (
            "twitch_account_id",
            "invalid_id",
            "invalid literal for int() with base 10: 'invalid_id'",
        ),
        ("login_name", "invalid_login!", "string does not match regex"),
        ("account_type", "invalid_type", "unexpected value; permitted"),
        ("broadcaster_type", "invalid_broadcaster", "unexpected value; permitted"),
        ("lifetime_view_count", -1, "ensure this value is greater than or equal to 0"),
        (
            "account_created_at",
            "invalid_date",
            "Invalid isoformat string: 'invalid_date' (type=value_error)",
        ),
    ],
)
def test_twitch_user_data_create_invalid(
    field: str, value: str, expected_error: str
) -> None:
    """Test creating a TwitchUserDataCreate with invalid data."""
    data = {
        "twitch_account_id": 123456,
        "login_name": "validlogin",
        "account_type": "",
        "broadcaster_type": "",
        "lifetime_view_count": 1000,
        "account_created_at": "2013-06-03T19:12:02Z",
        "first_sighting_as_viewer": None,
        "most_recent_sighting_as_viewer": None,
        "most_recent_concurrent_channel_count": None,
        "all_time_high_concurrent_channel_count": None,
        "all_time_high_at": None,
    }
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        TwitchUserDataCreate(**data)
    assert expected_error in str(excinfo.value)


def test_twitch_user_data_app_data():
    # Example Twitch API 'Get Stream' response
    api_response = {
        "id": 987654321,
        "user_id": 123456789,
        "user_login": "example_login",
        "game_id": "494131",
        "game_name": "Little Nightmares",
        "type": "live",
        "title": "hablamos y le damos a Little Nightmares 1",
        "tags": ["Español"],
        "viewer_count": 78365,
        "started_at": "2021-03-10T15:04:21Z",
        "language": "es",
        "thumbnail_url": "some_url_here",
        "tag_ids": [],
        "is_mature": False,
    }

    # Create a TwitchUserDataAppData instance from the API response
    user_data = TwitchUserDataFromGetStreamAPIResponse(**api_response)

    # Assertions to check the model has correctly parsed the data
    assert user_data.twitch_account_id == 123456789
    assert user_data.login_name == "example_login"
