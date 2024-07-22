from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from server.models.stream_viewerlist_fetch import (
    GetStreamResponse,
    StreamViewerListFetchCreate,
    StreamViewerListFetchRead,
    StreamViewerListFetchStatus,
)

VALID_DATA = {
    "fetch_action_at": datetime.now(),
    "duration_of_fetch_action": 1.5,
    "fetch_status": StreamViewerListFetchStatus.PENDING,
    "channel_owner_id": 12345,
    "category_id": 67890,
    "viewer_count": 100,
    "stream_id": 98765,
    "stream_started_at": datetime.now() - timedelta(hours=1),
    "language": "en",
    "is_mature": False,
    "was_live": True,
}

MOCK_GET_STREAM_RESPONSE = {
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


def test_workflow():
    response = GetStreamResponse(**MOCK_GET_STREAM_RESPONSE)

    assert response.channel_owner_id == int(MOCK_GET_STREAM_RESPONSE["user_id"])
    assert response.category_id == int(MOCK_GET_STREAM_RESPONSE["game_id"])
    assert response.viewer_count == int(MOCK_GET_STREAM_RESPONSE["viewer_count"])
    assert response.stream_id == int(MOCK_GET_STREAM_RESPONSE["id"])
    assert response.stream_started_at == datetime.fromisoformat(
        MOCK_GET_STREAM_RESPONSE["started_at"]
    )
    assert response.language == MOCK_GET_STREAM_RESPONSE["language"]
    assert response.is_mature == (
        MOCK_GET_STREAM_RESPONSE["is_mature"].lower() == "true"
    )
    assert response.was_live == (MOCK_GET_STREAM_RESPONSE["type"] == "live")

    fetch = StreamViewerListFetchCreate(
        fetch_action_at=datetime.now(timezone.utc),
        scanning_session_id="12345678-1234-1234-1234-123456789abc",
        **response.model_dump()
    )

    assert fetch.channel_owner_id == response.channel_owner_id
    assert fetch.category_id == response.category_id
    assert fetch.viewer_count == response.viewer_count
    assert fetch.stream_id == response.stream_id
    assert fetch.stream_started_at == response.stream_started_at
    assert fetch.language == response.language
    assert fetch.is_mature == response.is_mature
    assert fetch.was_live == response.was_live
    assert fetch.fetch_action_at is not None
    assert fetch.scanning_session_id == UUID("12345678-1234-1234-1234-123456789abc")
    assert fetch.fetch_status == StreamViewerListFetchStatus.PENDING
    assert fetch.duration_of_fetch_action is None


@pytest.mark.parametrize(
    "key, value",
    [
        ("fetch_action_at", datetime.now()),
        ("duration_of_fetch_action", 1.5),
        ("fetch_status", StreamViewerListFetchStatus.PENDING),
        ("channel_owner_id", 12345),
        ("category_id", 67890),
        ("viewer_count", 100),
        ("stream_id", 98765),
        ("stream_started_at", datetime.now() - timedelta(hours=1)),
        ("language", "en"),
        ("is_mature", False),
        ("was_live", True),
    ],
)
def test_stream_viewerlist_fetch_create(key, value):
    valid_data = VALID_DATA.copy()
    valid_data[key] = value
    fetch = StreamViewerListFetchCreate(**valid_data)
    assert fetch.model_dump()[key] == value


@pytest.mark.parametrize(
    "key, value",
    [
        ("fetch_action_at", "not a datetime"),
        ("duration_of_fetch_action", -1.5),
        ("fetch_status", "invalid status"),
        ("channel_owner_id", -12345),
        ("category_id", -67890),
        ("viewer_count", -100),
        ("stream_id", "not an int"),
        ("stream_started_at", "not a datetime"),
        ("language", "invalid_language_code!"),
        ("is_mature", "not a bool"),
        ("was_live", "not a bool"),
    ],
)
def test_stream_viewerlist_fetch_create_invalid(key, value):
    invalid_data = VALID_DATA.copy()
    invalid_data[key] = value
    with pytest.raises(ValidationError):
        StreamViewerListFetchCreate(**invalid_data)


@pytest.mark.parametrize(
    "key, value",
    [
        ("fetch_id", uuid4()),
        ("scanning_session_id", uuid4()),
        ("channel_owner_id", 12345),
        ("category_id", 67890),
    ],
)
def test_stream_viewerlist_fetch_read(key, value):
    valid_data = VALID_DATA.copy()
    valid_data["fetch_id"] = uuid4()
    valid_data["scanning_session_id"] = uuid4()
    valid_data[key] = value
    fetch = StreamViewerListFetchRead(**valid_data)
    assert fetch.model_dump()[key] == value


@pytest.mark.parametrize(
    "key, value",
    [
        ("fetch_id", "not a UUID"),
        ("scanning_session_id", "not a UUID"),
        ("channel_owner_id", -12345),
        ("category_id", -67890),
    ],
)
def test_stream_viewerlist_fetch_read_invalid(key, value):
    invalid_data = VALID_DATA.copy()
    invalid_data["fetch_id"] = uuid4()
    invalid_data["scanning_session_id"] = uuid4()
    invalid_data[key] = value
    with pytest.raises(ValidationError):
        StreamViewerListFetchRead(**invalid_data)
