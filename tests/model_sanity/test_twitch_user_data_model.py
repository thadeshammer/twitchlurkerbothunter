from datetime import datetime

import pytest
from sqlmodel import select

from server.models import (
    TwitchAccountType,
    TwitchBroadcasterType,
    TwitchUserData,
    TwitchUserDataCreate,
    TwitchUserDataRead,
)

TWITCH_USER_DATA_MOCK = {
    "twitch_account_id": 12345,
    "login_name": "sampleuser",
    "account_type": TwitchAccountType.NORMAL,
    "broadcaster_type": TwitchBroadcasterType.AFFILIATE,
    "lifetime_view_count": 1000,
    "account_created_at": "2020-12-12T20:12:00Z",
    "first_sighting_as_viewer": "2024-07-14T20:00:00Z",
    "most_recent_sighting_as_viewer": "2024-07-14T20:00:00Z",
    "most_recent_concurrent_channel_count": 10,
    "all_time_high_concurrent_channel_count": 20,
    "all_time_high_at": "2024-07-14T20:00:00Z",
}


@pytest.mark.asyncio
async def test_create_and_read_twitch_user_data(async_session):
    # Create a new entry using TwitchUserDataCreate
    create_data = TwitchUserDataCreate(**TWITCH_USER_DATA_MOCK)
    twitch_user_data = TwitchUserData(**create_data.model_dump())

    async with async_session.begin():
        async_session.add(twitch_user_data)

    await async_session.commit()

    # Read the entry back using TwitchUserDataRead
    statement = select(TwitchUserData).where(TwitchUserData.twitch_account_id == 12345)
    result = (await async_session.execute(statement)).scalar_one_or_none()

    assert isinstance(result, TwitchUserData)

    read_data = TwitchUserDataRead(**result.model_dump())

    assert read_data.twitch_account_id == TWITCH_USER_DATA_MOCK["twitch_account_id"]
    assert read_data.login_name == TWITCH_USER_DATA_MOCK["login_name"]
    assert read_data.account_type == TwitchAccountType(
        TWITCH_USER_DATA_MOCK["account_type"]
    )
    assert read_data.broadcaster_type == TwitchBroadcasterType(
        TWITCH_USER_DATA_MOCK["broadcaster_type"]
    )
    assert read_data.lifetime_view_count == TWITCH_USER_DATA_MOCK["lifetime_view_count"]
    assert (
        read_data.most_recent_concurrent_channel_count
        == TWITCH_USER_DATA_MOCK["most_recent_concurrent_channel_count"]
    )
    assert (
        read_data.all_time_high_concurrent_channel_count
        == TWITCH_USER_DATA_MOCK["all_time_high_concurrent_channel_count"]
    )
