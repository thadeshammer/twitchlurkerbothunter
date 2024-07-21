from datetime import datetime

import pytest
from sqlmodel import col, desc, select

from server.models import (
    StreamCategory,
    SuspectedBot,
    SuspectedBotCreate,
    SuspicionLevel,
    SuspicionReason,
    TwitchUserData,
    TwitchUserDataCreate,
)


@pytest.fixture
def valid_twitch_user_data():
    return [
        TwitchUserDataCreate(
            twitch_account_id=1,
            login_name="regular_streamer",
            account_type="",
            broadcaster_type="affiliate",
            account_created_at=datetime.now(),
            first_sighting_as_viewer=datetime.now(),
            most_recent_sighting_as_viewer=datetime.now(),
            most_recent_concurrent_channel_count=4,
            all_time_high_concurrent_channel_count=9,
            all_time_high_at=datetime.now(),
        ),
        TwitchUserDataCreate(
            twitch_account_id=2,
            login_name="guilty_person",
            account_type="",
            broadcaster_type="",
            account_created_at=datetime.now(),
            first_sighting_as_viewer=datetime.now(),
            most_recent_sighting_as_viewer=datetime.now(),
            most_recent_concurrent_channel_count=30,
            all_time_high_concurrent_channel_count=50000,
            all_time_high_at=datetime.now(),
        ),
        TwitchUserDataCreate(
            twitch_account_id=3,
            login_name="avid_viewer",
            account_type="",
            broadcaster_type="affiliate",
            account_created_at=datetime.now(),
            first_sighting_as_viewer=datetime.now(),
            most_recent_sighting_as_viewer=datetime.now(),
            most_recent_concurrent_channel_count=5,
            all_time_high_concurrent_channel_count=15,
            all_time_high_at=datetime.now(),
        ),
    ]


@pytest.fixture
def valid_stream_category():
    return StreamCategory(
        category_id=1,
        category_name="TestCategory",
    )


# pylint: disable=redefined-outer-name
@pytest.mark.asyncio
async def test_database_interactions(
    async_session, valid_twitch_user_data, valid_stream_category
):
    # Insert the TwitchUserData entries
    for user_data in valid_twitch_user_data:
        user = TwitchUserData(**user_data.model_dump())
        async_session.add(user)
    await async_session.commit()

    # Insert the StreamCategory entry
    async_session.add(valid_stream_category)
    await async_session.commit()

    # Query for the TwitchUserData with all_time_high_concurrent_channel_count greater than 1000
    statement = (
        select(TwitchUserData)
        .where(
            col(TwitchUserData.all_time_high_concurrent_channel_count).isnot(None)
            & TwitchUserData.all_time_high_concurrent_channel_count
            > 1000
        )
        .order_by(desc(TwitchUserData.all_time_high_concurrent_channel_count))
    )
    results = (await async_session.execute(statement)).all()

    # Create new SuspectedBot entries from the results
    for result in results:
        suspected_bot_data = SuspectedBotCreate(
            twitch_account_id=result.twitch_account_id,
            suspicion_level=SuspicionLevel.RED,
            suspicion_reason=SuspicionReason.CONCURRENT_CHANNEL_COUNT,
            is_banned_or_deleted=False,
        )
        suspected_bot = SuspectedBot(**suspected_bot_data.model_dump())
        async_session.add(suspected_bot)
    await async_session.commit()

    # Assert the correctness of the SuspectedBot entries
    for result in results:
        suspected_bot = (
            await async_session.execute(
                select(SuspectedBot).where(
                    SuspectedBot.twitch_account_id == result.twitch_account_id
                )
            )
        ).scalar_one_or_none()
        assert suspected_bot is not None
        assert suspected_bot.suspicion_level == SuspicionLevel.RED
        assert (
            suspected_bot.suspicion_reason == SuspicionReason.CONCURRENT_CHANNEL_COUNT
        )
        assert not suspected_bot.is_banned_or_deleted
