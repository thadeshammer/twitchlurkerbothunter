from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.scanning_session import (
    ScanningSessionCreate,
    ScanningSessionStopReasonEnum,
)

# Define valid data for the ScanningSessionCreate model
VALID_DATA = {
    "time_started": datetime.now(),
    "streams_in_scan": 5,
}


def test_scanning_session_create_valid():
    # Test creating a ScanningSessionCreate with valid data
    session = ScanningSessionCreate(**VALID_DATA)
    assert session.time_started == VALID_DATA["time_started"]
    assert session.streams_in_scan == VALID_DATA["streams_in_scan"]
    assert session.reason_ended == ScanningSessionStopReasonEnum.UNSPECIFIED


def test_scanning_session_create_missing_required_fields():
    # Test creating a ScanningSessionCreate without required fields
    invalid_data = VALID_DATA.copy()
    invalid_data.pop("time_started")
    with pytest.raises(ValidationError):
        ScanningSessionCreate(**invalid_data)

    invalid_data = VALID_DATA.copy()
    invalid_data.pop("streams_in_scan")
    with pytest.raises(ValidationError):
        ScanningSessionCreate(**invalid_data)


def test_scanning_session_create_invalid_streams_in_scan():
    # Test creating a ScanningSessionCreate with invalid streams_in_scan
    invalid_data = VALID_DATA.copy()
    invalid_data["streams_in_scan"] = 0
    with pytest.raises(ValidationError):
        ScanningSessionCreate(**invalid_data)

    invalid_data["streams_in_scan"] = -1
    with pytest.raises(ValidationError):
        ScanningSessionCreate(**invalid_data)


def test_scanning_session_create_valid_optional_fields():
    # Test creating a ScanningSessionCreate with all valid optional fields
    valid_data = VALID_DATA.copy()
    valid_data.update(
        {
            "time_ended": datetime.now() + timedelta(hours=1),
            "reason_ended": ScanningSessionStopReasonEnum.COMPLETE,
            "viewerlists_fetched": 10,
            "average_time_per_fetch": 1.5,
            "average_time_for_get_user_call": 0.5,
            "average_time_for_get_stream_call": 0.7,
            "suspects_spotted": 2,
            "error_count": 1,
        }
    )
    session = ScanningSessionCreate(**valid_data)
    assert session.viewerlists_fetched == 10
    assert session.average_time_per_fetch == 1.5
    assert session.average_time_for_get_user_call == 0.5
    assert session.average_time_for_get_stream_call == 0.7
    assert session.suspects_spotted == 2
    assert session.error_count == 1


@pytest.mark.parametrize(
    "key, value",
    [
        ("viewerlists_fetched", -1),
        ("average_time_per_fetch", -1.0),
        ("average_time_for_get_user_call", -0.5),
        ("average_time_for_get_stream_call", -0.7),
        ("suspects_spotted", -2),
        ("error_count", -1),
        ("reason_ended", "dehydrated"),
    ],
)
def test_scanning_session_create_invalid_optional_fields(key, value):
    # Test creating a ScanningSessionCreate with invalid optional fields
    invalid_data = VALID_DATA.copy()
    invalid_data.update({key: value})
    with pytest.raises(ValidationError):
        ScanningSessionCreate(**invalid_data)
