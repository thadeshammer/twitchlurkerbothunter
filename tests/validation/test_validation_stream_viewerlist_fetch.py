from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    StreamViewerListFetchAppData,
    StreamViewerListFetchCreate,
    StreamViewerListFetchStatus,
    StreamViewerListFetchTwitchAPIResponse,
    merge_stream_viewerlist_fetch_data,
)

# Mock valid responses
MOCK_TWITCH_API_RESPONSE = {
    "id": "9876543210",
    "user_id": "1234567890",
    "game_id": "10",
    "type": "live",
    "started_at": str(datetime.now(timezone.utc).isoformat()),
    "viewer_count": "1500",
    "language": "en",
    "is_mature": "True",
}

MOCK_APP_DATA = {
    "fetch_action_at": datetime.now(timezone.utc).isoformat(),
    "duration_of_fetch_action": 2.5,
    "scanning_session_id": uuid4(),
    "fetch_status": StreamViewerListFetchStatus.WAITING_ON_VIEWER_LIST,
}


def test_stream_viewerlist_fetch_twitch_api_response_valid():
    """Test creating a StreamViewerListFetchTwitchAPIResponse with valid data."""
    response = StreamViewerListFetchTwitchAPIResponse(**MOCK_TWITCH_API_RESPONSE)
    assert response.viewer_count == 1500
    assert response.stream_id == 9876543210
    assert response.stream_started_at == datetime.fromisoformat(
        MOCK_TWITCH_API_RESPONSE["started_at"]
    )
    assert response.language == "en"
    assert response.is_mature is True
    assert response.was_live is True


def test_stream_viewerlist_fetch_create_valid():
    """Test creating a StreamViewerListFetchCreate with valid data."""
    api_data = StreamViewerListFetchTwitchAPIResponse(**MOCK_TWITCH_API_RESPONSE)
    app_data = StreamViewerListFetchAppData(**MOCK_APP_DATA)
    combined_data: StreamViewerListFetchCreate = merge_stream_viewerlist_fetch_data(
        api_data, app_data
    )
    assert combined_data.viewer_count == 1500
    assert combined_data.stream_id == 9876543210
    assert combined_data.stream_started_at == datetime.fromisoformat(
        MOCK_TWITCH_API_RESPONSE["started_at"]
    )
    assert combined_data.language == "en"
    assert combined_data.is_mature is True
    assert combined_data.was_live is True
    assert combined_data.category_id == 10
    assert (
        combined_data.fetch_status == StreamViewerListFetchStatus.WAITING_ON_VIEWER_LIST
    )
    assert combined_data.fetch_action_at == datetime.fromisoformat(
        MOCK_APP_DATA["fetch_action_at"]
    )
    assert combined_data.duration_of_fetch_action == 2.5
    assert combined_data.scanning_session_id == MOCK_APP_DATA["scanning_session_id"]
    assert combined_data.channel_owner_id == 1234567890


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("viewer_count", -1, "ensure this value is greater than or equal to 0"),
        ("id", "invalid_id", "value is not a valid integer"),
        ("started_at", "invalid_date", "invalid datetime format"),
        ("language", "invalid_language", "string does not match regex"),
        ("is_mature", "not_a_bool", "value could not be parsed to a boolean"),
        (
            "type",
            "invalid_type",
            "Could not convert 'type' in Twitch response. (type=value_error)",
        ),
    ],
)
def test_stream_viewerlist_fetch_twitch_api_response_invalid(
    field, value, expected_error
):
    """Test creating a StreamViewerListFetchTwitchAPIResponse with invalid data."""
    data = MOCK_TWITCH_API_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        StreamViewerListFetchTwitchAPIResponse(**data)
    assert expected_error in str(excinfo.value)


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("fetch_action_at", "invalid_date", "invalid datetime format"),
        (
            "duration_of_fetch_action",
            -1,
            "ensure this value is greater than or equal to 0",
        ),
        ("scanning_session_id", "invalid_uuid", "value is not a valid uuid"),
        (
            "fetch_status",
            "invalid_enum_member",
            "value is not a valid enumeration member",
        ),
        ("scanning_session_id", "invalid_uuid", "value is not a valid uuid"),
    ],
)
def test_stream_viewerlist_fetch_create_invalid(field, value, expected_error):
    """Test creating a StreamViewerListFetchCreate with invalid data."""
    data = MOCK_APP_DATA.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        StreamViewerListFetchAppData(**data)
    assert expected_error in str(excinfo.value)
