from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.stream_viewerlist_fetch import (
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
