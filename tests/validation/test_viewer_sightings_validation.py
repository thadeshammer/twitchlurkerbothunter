import pytest
from marshmallow import ValidationError

from app.models import ViewerSighting, ViewerSightingSchema


@pytest.mark.parametrize(
    "invalid_viewer_login_name",
    [
        "invalid!username!",
        "this_name_will_definitely_be_much_much_too_long_for_a_twitch_user_name_ok",
        "",
        "无效",  # Mandarin for "invalid" (wúxiào)
        123,
    ],
)
def test_create_invalid_viewer_sighting_username(session, invalid_viewer_login_name):
    invalid_data = {
        "viewer_login_name": invalid_viewer_login_name,
        "processed_by_user_data_enricher": False,
        "processed_by_user_sighting_aggregator": True,
    }

    schema = ViewerSightingSchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load(invalid_data, session=session)

    errors = excinfo.value.messages
    assert "viewer_login_name" in errors


def test_create_valid_viewer_sighting(session):
    data = {
        "viewer_login_name": "thadeshammer",
    }

    schema = ViewerSightingSchema()
    vs: ViewerSighting = schema.load(data, session=session)

    assert vs.viewer_login_name == "thadeshammer"
