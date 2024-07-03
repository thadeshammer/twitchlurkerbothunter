from app.models import SuspectedBotCreate, SuspicionLevel, SuspicionReason


def test_suspected_bot_create():
    sus = SuspectedBotCreate(
        suspicion_level=SuspicionLevel.RED,
        suspicion_reason=SuspicionReason.CONCURRENT_CHANNEL_COUNT,
    )

    assert sus.additional_notes is None
    assert sus.has_ever_streamed is None
    assert sus.follower_count is None
    assert sus.following_count is None

    assert sus.is_banned_or_deleted is False
