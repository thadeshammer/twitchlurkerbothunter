import pytest
from marshmallow import ValidationError

from app.models import TwitchUserData, TwitchUserDataInternal, TwitchUserDataSchema


@pytest.mark.parametrize(
    "field , value",
    [
        ("id", "not_a_number"),
        ("id", ""),
        ("login", "invalid!username!"),
        (
            "login",
            "this_name_will_definitely_be_much_much_too_long_for_a_twitch_user_name_ok",
        ),
        ("login", ""),
        ("login", "无效"),  # Mandarin for "invalid" (wúxiào)
        ("login", 123),
        ("type", "not_an_account_type"),
        ("broadcaster_type", "not_a_broadcaster_type"),
    ],
)
def test_create_invalid_twitch_user_data(session, field, value):
    data = {
        "id": "1234567890",
        "login": "thadeshammer",
        "type": "",
        "broadcaster_type": "affiliate",
    }

    data[field] = value

    schema = TwitchUserDataSchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load(data, session=session)

    errors = excinfo.value.messages
    assert field in errors


def test_create_valid_twitch_user_data(session):
    # Example API response

    # api_response = {
    #     "id": 123456,
    #     "login": "example_user",
    #     "display_name": "ExampleUser",
    #     "type": "",
    #     "broadcaster_type": "",
    #     "view_count": 1000,
    #     "created_at": "2013-06-03T19:12:02Z"
    # }
    api_response = {
        "id": "1234567890",
        "login": "thadeshammer",
        "display_name": "ThadesHammer",
        "type": "",
        "broadcaster_type": "affiliate",
        "view_count": "4",
        "created_at": "2013-06-03T19:12:02Z",
    }
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc)
    app_data = TwitchUserDataInternal(
        first_sighting_as_viewer=str(timestamp),
        most_recent_sighting_as_viewer=str(timestamp),
        all_time_high_at=str(timestamp),
        most_recent_concurrent_channel_count=3,
        all_time_high_concurrent_channel_count=5,
    )

    from dataclasses import asdict

    full_data = api_response | asdict(app_data)

    schema = TwitchUserDataSchema()
    vs: TwitchUserData = schema.load(full_data, session=session)

    assert vs.twitch_account_id == 1234567890
    assert vs.login_name == "thadeshammer"
    assert vs.account_type == ""
    assert vs.broadcaster_type == "affiliate"
    assert vs.has_been_enriched is False
    # assert vs.account_created_at == datetime.strptime(
    #     "2013-06-03T19:12:02Z", "%YYYY-%mm-%dd %H:%M:%S%Z"
    # )
    assert vs.most_recent_concurrent_channel_count == 3
