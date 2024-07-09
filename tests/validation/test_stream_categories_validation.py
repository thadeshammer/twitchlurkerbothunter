from app.models import StreamCategoryCreate

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


def test_category_create():
    data = GET_STREAM_MOCK.copy()
    sc = StreamCategoryCreate(**data)

    assert sc.category_id == int(GET_STREAM_MOCK["game_id"])
    assert sc.category_name == GET_STREAM_MOCK["game_name"]

    simple = StreamCategoryCreate(
        **{"category_name": "Just Chatting", "category_id": 1}
    )

    assert simple.category_id == 1
    assert simple.category_name == "Just Chatting"
