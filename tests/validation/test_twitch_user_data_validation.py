import pytest
from marshmallow import ValidationError

from app.models import TwitchUserData, TwitchUserDataSchema


@pytest.mark.parametrize(
    "field , value",
    [
        ("twitch_account_id", "not_a_number"),
        ("twitch_account_id", ""),
        ("login_name", "invalid!username!"),
        (
            "login_name",
            "this_name_will_definitely_be_much_much_too_long_for_a_twitch_user_name_ok",
        ),
        ("login_name", ""),
        ("login_name", "无效"),  # Mandarin for "invalid" (wúxiào)
        ("login_name", 123),
        ("account_type", "not_an_account_type"),
        ("broadcaster_type", "not_a_broadcaster_type"),
    ],
)
def test_create_invalid_twitch_user_data(session, field, value):
    data = {
        "twitch_account_id": "1234567890",
        "login_name": "thadeshammer",
        "account_type": "",
        "broadcaster_type": "affiliate",
    }

    data[field] = value

    schema = TwitchUserDataSchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load(data, session=session)

    errors = excinfo.value.messages
    assert field in errors


def test_create_valid_twitch_user_data(session):
    data = {
        "twitch_account_id": "1234567890",
        "login_name": "thadeshammer",
        "account_type": "",
        "broadcaster_type": "affiliate",
    }

    schema = TwitchUserDataSchema()
    print(f"{schema=}")
    vs: TwitchUserData = schema.load(data, session=session)

    assert vs.twitch_account_id == 1234567890
    assert vs.login_name == "thadeshammer"
    assert vs.account_type == ""
    assert vs.broadcaster_type == "affiliate"
    assert vs.has_been_enriched is False
