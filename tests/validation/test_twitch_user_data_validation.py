# import pytest

from app.models.twitch_user_data import TwitchUserDataCreate

# GET_USER_MOCK = {
#     "id": "141981764",
#     "login": "twitchdev",
#     "display_name": "TwitchDev",
#     "type": "",
#     "broadcaster_type": "partner",
#     "description": "Supporting third-party developers building Twitch integrations from chatbots to game integrations.",
#     "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png",
#     "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png",
#     "view_count": "5980557",
#     "email": "not-real@email.com",
#     "created_at": "2016-12-14T20:32:28Z",
# }

# GET_STREAMS_MOCK = {
#     "id": "123456789",
#     "user_id": "98765",
#     "user_login": "sandysanderman",
#     "user_name": "SandySanderman",
#     "game_id": "494131",
#     "game_name": "Little Nightmares",
#     "type": "live",
#     "title": "hablamos y le damos a Little Nightmares 1",
#     "tags": ["Español"],
#     "viewer_count": "78365",
#     "started_at": "2021-03-10T15:04:21Z",
#     "language": "es",
#     "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/live_user_auronplay-{width}x{height}.jpg",
#     "tag_ids": [],
#     "is_mature": "false",
# }


# def test_create_from_get_user():
#     tud = TwitchUserDataCreate(**GET_USER_MOCK)

#     assert tud.twitch_account_id == GET_USER_MOCK["id"]
#     assert tud.login_name == GET_USER_MOCK["name"]
