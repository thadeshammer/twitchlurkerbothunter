# tests/validation/test_validation_stream_categories.py
import pytest
from pydantic import ValidationError

from app.models.stream_categories import StreamCategoryCreate, StreamCategoryRead

# Mock valid responses
MOCK_STREAM_CATEGORY_API_RESPONSE = {
    "game_id": "12345",
    "game_name": "Just Chatting",
}


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        (
            "game_name",
            "invalid!category_with_long_name_exceeding_25_characters",
            "ensure this value has at most 25 characters",
        ),
        ("game_id", "-2", "ensure this value is greater than or equal to -1"),
    ],
)
def test_stream_category_create_invalid(field, value, expected_error):
    """Test creating a StreamCategoryCreate with invalid data."""
    data = MOCK_STREAM_CATEGORY_API_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        StreamCategoryCreate(**data)
    assert expected_error in str(excinfo.value)


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("game_id", "-2", "ensure this value is greater than or equal to -1"),
        (
            "game_name",
            "invalid!category_with_long_name_exceeding_25_characters",
            "ensure this value has at most 25 characters",
        ),
    ],
)
def test_stream_category_read_invalid(field, value, expected_error):
    """Test creating a StreamCategoryRead with invalid data."""
    data = MOCK_STREAM_CATEGORY_API_RESPONSE.copy()
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        StreamCategoryRead(**data)
    assert expected_error in str(excinfo.value)


def test_stream_category_create_valid():
    """Test creating a StreamCategoryCreate with valid data."""
    data = MOCK_STREAM_CATEGORY_API_RESPONSE.copy()
    instance = StreamCategoryCreate(**data)
    assert instance.category_id == 12345
    assert instance.category_name == "Just Chatting"


def test_stream_category_read_valid():
    """Test creating a StreamCategoryRead with valid data."""
    data = MOCK_STREAM_CATEGORY_API_RESPONSE.copy()
    instance = StreamCategoryRead(**data)
    assert instance.category_id == 12345
    assert instance.category_name == "Just Chatting"
