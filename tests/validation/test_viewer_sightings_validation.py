from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.viewer_sightings import ViewerSighting


def test_create_valid_viewer_sighting():
    valid_data = {
        "viewer_login_name": "valid_username",
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": False,
        "viewerlist_fetch_id": uuid4(),
    }

    viewer_sighting = ViewerSighting(**valid_data)
    assert viewer_sighting.viewer_login_name == "valid_username"
    assert viewer_sighting.processed_by_user_data_enricher is False
    assert viewer_sighting.processed_by_user_sighting_aggregator is False
    assert viewer_sighting.viewerlist_fetch_id is not None
    assert viewer_sighting.id is not None


def test_create_invalid_viewer_sighting_username():
    invalid_data = {
        "viewer_login_name": "invalid!username!",
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": False,
        "viewerlist_fetch_id": uuid4(),
    }

    with pytest.raises((ValueError, ValidationError)):
        print(f"\n > > > {invalid_data=} < < < \n")
        vs = ViewerSighting(**invalid_data)
        print(f"\n > > > {vs.viewer_login_name=} < < < \n")
    assert vs.viewer_login_name != invalid_data["viewer_login_name"]


def test_create_invalid_viewer_sighting_missing_field():
    invalid_data = {
        "viewer_login_name": "valid_username",
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": False,
        # Missing viewerlist_fetch_id
    }

    with pytest.raises(ValidationError):
        ViewerSighting(**invalid_data)
