from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.viewer_sightings import ViewerSightingCreate


def test_create_valid_viewer_sighting():
    uid = uuid4()

    valid_data = {
        "viewer_login_name": "valid_username",
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": False,
        "viewerlist_fetch_id": uid,
    }

    viewer_sighting = ViewerSightingCreate(**valid_data)
    assert viewer_sighting.viewer_login_name == "valid_username"
    assert viewer_sighting.processed_by_user_data_enricher is False
    assert viewer_sighting.processed_by_user_sighting_aggregator is False
    assert viewer_sighting.viewerlist_fetch_id == uid


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("viewer_login_name", ""),
        ("viewer_login_name", "this!shouldnt'work!"),
        ("viewer_login_name", "spaces are no good"),
        ("viewer_login_name", "名字"),
        ("viewer_login_name", "имя"),
        ("viewer_login_name", "ชื่อ"),
        ("viewerlist_fetch_id", ""),
        ("viewerlist_fetch_id", "nope"),
    ],
)
def test_create_invalid_viewer_sighting(key, value):
    invalid_data = {
        "viewer_login_name": "legit_user",
        "viewerlist_fetch_id": uuid4(),
    }
    invalid_data[key] = value

    with pytest.raises((ValueError, ValidationError)):
        ViewerSightingCreate(**invalid_data)


def test_create_invalid_viewer_sighting_missing_field():
    invalid_data = {
        "viewer_login_name": "valid_username",
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": False,
        # Missing viewerlist_fetch_id
    }

    with pytest.raises(ValidationError):
        ViewerSightingCreate(**invalid_data)
