from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import ViewerSightingCreate, ViewerSightingRead

# Mock valid data
MOCK_VIEWER_SIGHTING_READ: dict[str, Any] = {
    "viewer_sighting_id": uuid4(),
    "viewerlist_fetch_id": uuid4(),
    "viewer_login_name": "validloginname",
}

MOCK_VIEWER_SIGHTING_CREATE = {
    "viewer_login_name": "validloginname",
}


def test_viewer_sighting_read_invalid():
    """Test creating a ViewerSightingRead with invalid data."""
    data: dict[str, Any] = MOCK_VIEWER_SIGHTING_READ.copy()
    data["viewer_login_name"] = "invalid_login!"
    with pytest.raises(ValidationError) as excinfo:
        ViewerSightingRead(**data)
    assert "string does not match regex" in str(excinfo.value)


def test_viewer_sighting_create_invalid():
    """Test creating a ViewerSightingCreate with invalid data."""
    data = MOCK_VIEWER_SIGHTING_CREATE.copy()
    data["viewer_login_name"] = "invalid_login!"
    with pytest.raises(ValidationError) as excinfo:
        ViewerSightingCreate(**data)
    assert "string does not match regex" in str(excinfo.value)


def test_viewer_sighting_create_valid():
    """Test creating a ViewerSightingCreate with valid data."""
    data = MOCK_VIEWER_SIGHTING_CREATE.copy()
    instance = ViewerSightingCreate(**data)
    assert instance.viewer_login_name == data["viewer_login_name"]


def test_viewer_sighting_read_valid():
    """Test creating a ViewerSightingRead with valid data."""
    data = MOCK_VIEWER_SIGHTING_READ.copy()
    instance = ViewerSightingRead(**data)
    assert instance.viewer_sighting_id == data["viewer_sighting_id"]
    assert instance.viewerlist_fetch_id == data["viewerlist_fetch_id"]
    assert instance.viewer_login_name == data["viewer_login_name"]
