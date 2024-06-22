from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    ScanningSessionCreate,
    ScanningSessionRead,
    ScanningSessionStopReasonEnum,
)

# Mock valid response
MOCK_SCANNING_SESSION_RESPONSE = {
    "scanning_session_id": uuid4(),
    "time_started": datetime.now(timezone.utc),
    "time_ended": datetime.now(timezone.utc),
    "reason_ended": ScanningSessionStopReasonEnum.COMPLETE,
    "streams_in_scan": 50,
    "viewerlists_fetched": 45,
    "average_time_per_fetch": 1.5,
    "average_time_for_get_user_call": 0.3,
    "average_time_for_get_stream_call": 0.2,
    "suspects_spotted": 10,
    "error_count": 2,
}


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("scanning_session_id", "invalid_uuid", "value is not a valid uuid"),
        ("time_started", "invalid_date", "invalid datetime format"),
        ("streams_in_scan", -1, "ensure this value is greater than 0"),
        ("viewerlists_fetched", -1, "ensure this value is greater than or equal to 0"),
        (
            "average_time_per_fetch",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        (
            "average_time_for_get_user_call",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        (
            "average_time_for_get_stream_call",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        ("suspects_spotted", -1, "ensure this value is greater than or equal to 0"),
        ("error_count", -1, "ensure this value is greater than or equal to 0"),
    ],
)
def test_scanning_session_read_invalid(field, value, expected_error):
    """Test creating a ScanningSessionRead with invalid data."""
    data = MOCK_SCANNING_SESSION_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        ScanningSessionRead(**data)
    assert expected_error in str(excinfo.value)


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("time_started", "invalid_date", "invalid datetime format"),
        ("streams_in_scan", -1, "ensure this value is greater than 0"),
        ("viewerlists_fetched", -1, "ensure this value is greater than or equal to 0"),
        (
            "average_time_per_fetch",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        (
            "average_time_for_get_user_call",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        (
            "average_time_for_get_stream_call",
            -1.0,
            "ensure this value is greater than or equal to 0",
        ),
        ("suspects_spotted", -1, "ensure this value is greater than or equal to 0"),
        ("error_count", -1, "ensure this value is greater than or equal to 0"),
    ],
)
def test_scanning_session_create_invalid(field, value, expected_error):
    """Test creating a ScanningSessionCreate with invalid data."""
    data = MOCK_SCANNING_SESSION_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        ScanningSessionCreate(**data)
    assert expected_error in str(excinfo.value)


def test_scanning_session_read_valid():
    """Test creating a ScanningSessionRead with valid data."""
    valid_data = MOCK_SCANNING_SESSION_RESPONSE.copy()
    try:
        ScanningSessionRead(**valid_data)
    except ValidationError:
        pytest.fail("Valid data raised ValidationError")


def test_scanning_session_create_valid():
    """Test creating a ScanningSessionCreate with valid data."""
    valid_data = {
        "time_started": datetime.now(timezone.utc),
        "streams_in_scan": 50,
    }
    try:
        ScanningSessionCreate(**valid_data)
    except ValidationError:
        pytest.fail("Valid data raised ValidationError")
