import pytest
from pydantic import ValidationError

from server.models.suspected_bot import (
    SuspectedBotCreate,
    SuspicionLevel,
    SuspicionReason,
)

VALID_DATA = {
    "suspicion_level": SuspicionLevel.RED,
    "suspicion_reason": SuspicionReason.CONCURRENT_CHANNEL_COUNT,
    "additional_notes": "Valid notes.",
    "twitch_account_id": 123,
    "has_ever_streamed": None,
    "follower_count": 100,
    "following_count": 50,
    "is_banned_or_deleted": False,
}


@pytest.mark.parametrize(
    "key, value",
    [
        ("suspicion_level", "invalid_level"),
        ("suspicion_reason", "invalid_reason"),
        ("additional_notes", "Invalid characters: 英語でメモを書いてください"),
        ("has_ever_streamed", "not_a_boolean"),
        ("follower_count", -10),
        ("following_count", -20),
        ("is_banned_or_deleted", "not_a_boolean"),
    ],
)
def test_invalid_suspected_bot_create(key, value):
    invalid_data = VALID_DATA.copy()
    invalid_data[key] = value

    with pytest.raises(ValidationError):
        SuspectedBotCreate(**invalid_data)


def test_valid_suspected_bot_create():
    valid_data = VALID_DATA.copy()
    bot = SuspectedBotCreate(**valid_data)
    assert bot.suspicion_level == valid_data["suspicion_level"]
    assert bot.suspicion_reason == valid_data["suspicion_reason"]
    assert bot.additional_notes == valid_data["additional_notes"]
    assert bot.has_ever_streamed == valid_data["has_ever_streamed"]
    assert bot.follower_count == valid_data["follower_count"]
    assert bot.following_count == valid_data["following_count"]
    assert bot.is_banned_or_deleted == valid_data["is_banned_or_deleted"]
