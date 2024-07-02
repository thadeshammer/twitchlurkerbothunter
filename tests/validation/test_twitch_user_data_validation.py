import pytest
from pydantic import ValidationError

from app.models.twitch_user_data import TwitchUserDataCreate
from app.util import convert_timestamp_from_twitch

GET_USER_MOCK = {
    "id": "141981764",
    "login": "weepwop1337socks",
    "display_name": "wEEpwOp1337socks",
    "type": "",
    "broadcaster_type": "affiliate",
    "description": "same ol same ol",
    "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/profile_image-300x300.png",
    "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/channel_offline.png",
    "view_count": "5980557",
    "email": "not-real@email.com",  # NOTE we do NOT scope for this; response will lack email.
    "created_at": "2016-12-14T20:32:28Z",
}

GET_STREAM_MOCK = {
    "id": "123456789",
    "user_id": "98765",
    "user_login": "sandysanderman",
    "user_name": "SandySanderman",
    "game_id": "494131",
    "game_name": "Little Nightmares",
    "type": "live",
    "title": "hablamos y le damos a Little Nightmares 1",
    "tags": ["Español"],
    "viewer_count": "78365",
    "started_at": "2021-03-10T15:04:21Z",
    "language": "es",
    "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/live_user_auronplay-{width}x{height}.jpg",
    "tag_ids": [],
    "is_mature": "false",
}


TWITCH_USER_DATA_MOCK = {
    "twitch_account_id": "141981764",
    "login_name": "weepwop1337socks",
    "account_type": "",
    "broadcaster_type": "affiliate",
    "view_count": "5980557",
    "created_at": "2016-12-14T20:32:28Z",
}


def test_create_from_get_user():
    data = GET_USER_MOCK.copy()
    assert isinstance(data, dict)
    tud = TwitchUserDataCreate(**data)

    assert tud.twitch_account_id == int(GET_USER_MOCK["id"])
    assert tud.login_name == GET_USER_MOCK["login"]
    assert tud.account_type == GET_USER_MOCK["type"]
    assert tud.broadcaster_type == GET_USER_MOCK["broadcaster_type"]
    assert tud.lifetime_view_count == int(GET_USER_MOCK["view_count"])

    assert tud.account_created_at is not None
    expected_timestamp = convert_timestamp_from_twitch(GET_USER_MOCK["created_at"])
    result_timestamp = tud.account_created_at.strftime("%Y-%m-%d %H:%M:%S%z")
    assert expected_timestamp == result_timestamp


@pytest.mark.parametrize(
    "key, value",
    [
        ("id", "#!%^^!"),
        ("id", "not_a_number"),
        ("id", "-4"),
        ("id", "3.1416"),
        ("login", "invalid characters!"),
        ("login", "名字"),
        ("login", "имя"),
        ("login", "ชื่อ"),
        ("type", "bestboi"),
        ("broadcaster_type", "afiliate"),
    ],
)
def test_create_against_invalid_data_get_user(key, value):
    assert isinstance(GET_USER_MOCK, dict)
    invalid_data = GET_USER_MOCK.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        TwitchUserDataCreate(**invalid_data)


def test_create_from_get_stream():
    tud = TwitchUserDataCreate(**GET_STREAM_MOCK)

    assert tud.twitch_account_id == int(GET_STREAM_MOCK["user_id"])
    assert tud.login_name == GET_STREAM_MOCK["user_login"]


@pytest.mark.parametrize(
    "key, value",
    [
        ("user_id", "#!%^^!"),
        ("user_id", "not_a_number"),
        ("user_id", "-4"),
        ("user_id", "3.1416"),
        ("user_login", "invalid characters!"),
        ("user_login", "名字"),
        ("user_login", "имя"),
        ("user_login", "ชื่อ"),
    ],
)
def test_create_against_invalid_data_get_stream(key, value):
    invalid_data = GET_STREAM_MOCK.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        TwitchUserDataCreate(**invalid_data)


@pytest.mark.parametrize(
    "key, value",
    [
        ("login_name", "invalid characters!"),
        ("login_name", "名字"),
        ("login_name", "имя"),
        ("login_name", "ชื่อ"),
        ("twitch_account_id", "not a number"),
    ],
)
def test_create_against_invalid_data_internal_definition(key, value):
    invalid_data = TWITCH_USER_DATA_MOCK.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        TwitchUserDataCreate(**invalid_data)
