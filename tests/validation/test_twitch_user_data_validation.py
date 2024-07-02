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


def test_create_from_get_user():
    tud = TwitchUserDataCreate(**GET_USER_MOCK)

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
        ("login_name", "invalid characters!"),
        ("login_name", "名字"),
        ("login_name", "имя"),
        ("login_name", "ชื่อ"),
        ("account_type", "bestboi"),
        ("broadcaster_type", "afiliate"),
    ],
)
def test_create_from_get_user_invalid(key, value):
    invalid_data = GET_USER_MOCK.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        TwitchUserDataCreate(**invalid_data)


def test_create_from_get_stream():
    tud = TwitchUserDataCreate(**GET_STREAM_MOCK)

    assert tud.twitch_account_id == int(GET_STREAM_MOCK["user_id"])
    assert tud.login_name == GET_STREAM_MOCK["user_login"]
