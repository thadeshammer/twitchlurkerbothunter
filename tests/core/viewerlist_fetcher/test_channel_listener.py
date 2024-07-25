# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from twitchio.errors import TwitchIOException

from server.core.viewerlist_fetcher import (
    ViewerListFetchData,
    VLFetcherChannelJoinError,
)
from server.core.viewerlist_fetcher.channel_listener import (
    ViewerListFetcherChannelListener,
)

logger = logging.getLogger("__name__")


@pytest.fixture
def fetcher():
    fetcher_instance = ViewerListFetcherChannelListener(
        worker_id="test_worker", access_token="test_token"
    )

    mock_ready_event = MagicMock(spec=asyncio.Event)
    mock_ready_event.is_set.return_value = True
    mock_ready_event.wait = MagicMock(return_value=None)
    fetcher_instance._ready_event = mock_ready_event

    return fetcher_instance


@pytest.mark.asyncio
async def test_event_raw_data_chatter_join_message(fetcher):
    # :user!user@user.tmi.twitch.tv JOIN #channel
    fetcher._user_lists = {"test_channel": ViewerListFetchData()}
    message = ":test_user!test_user@test_user.tmi.twitch.tv JOIN #test_channel"

    await fetcher.event_raw_data(message)

    assert fetcher._user_lists["test_channel"].user_names == {"test_user"}


@pytest.mark.asyncio
async def test_event_raw_data_combined_messages(fetcher):
    with patch.object(fetcher, "part_channels", new_callable=AsyncMock):
        channel_name = "coolstreamer"
        anonymized_real_sample_message = (
            ":legituser.tmi.twitch.tv 353 legituser = #coolstreamer :user01 user02 "
            "user03 user04 user05 user06 user07 user08 user09 user10 user11 user12 user13 user14 "
            "user15 user16 user17 user18 user19 user20 user21 user22 user23 user24 user25 user26 "
            "user27 user28 user29 user30 user31 user32\r\n"
            ":legituser.tmi.twitch.tv 353 legituser = #coolstreamer :user33 user34 "
            "user35 user36 user37 user38 user39 user40 user41 user42 user43 user44 user45 user46 "
            "user47 user48 user49 user50 user51 user52 user53 user54 user55 user56 user57\r\n"
            ":legituser.tmi.twitch.tv 353 legituser = #coolstreamer :legituser\r\n"
            ":legituser.tmi.twitch.tv 366 legituser #coolstreamer :End of /NAMES list\r\n"
        )
        user_list = set(
            ["user0" + str(n) if n < 10 else "user" + str(n) for n in range(1, 58)]
        )
        user_list.add("legituser")

        logger.debug(f"{anonymized_real_sample_message=}")
        fetcher._user_lists = {channel_name: ViewerListFetchData()}
        await fetcher.event_raw_data(anonymized_real_sample_message)
        logger.debug(f"{user_list=}")
        logger.debug(f"{fetcher._user_lists[channel_name].user_names}")
        assert user_list == fetcher._user_lists[channel_name].user_names


@pytest.mark.asyncio
async def test_event_raw_data_chatter_list_message(fetcher):
    fetcher._user_lists = {"test_channel": ViewerListFetchData()}
    message = ":tmi.twitch.tv 353 this_bot = #test_channel :user1 user2 user3"

    await fetcher.event_raw_data(message)

    assert fetcher._user_lists["test_channel"].user_names == {
        "user1",
        "user2",
        "user3",
    }


@pytest.mark.asyncio
async def test_event_raw_data_chatter_list_message_no_names(fetcher):
    fetcher._user_lists = {"test_channel": ViewerListFetchData()}
    message = ":tmi.twitch.tv 353 this_bot = #test_channel :"

    await fetcher.event_raw_data(message)

    assert len(fetcher._user_lists["test_channel"].user_names) == 0


@pytest.mark.asyncio
async def test_event_raw_data_leave_channel_message(fetcher):
    with patch.object(
        fetcher, "part_channels", new_callable=AsyncMock
    ) as mock_part_channels:

        channel = "test_channel"
        fetcher._user_lists = {channel: ViewerListFetchData()}
        message = f"lurkerbot:tmi.twitch.tv 366 lurkerbot {channel} :End of /NAMES list"
        logger.info(f"{message=} || {fetcher._user_lists.keys()=}")

        await fetcher.event_raw_data(message)

        mock_part_channels.assert_called_with(channel)


@pytest.mark.asyncio
async def test_join_channel_success(fetcher):
    with patch.object(
        fetcher, "join_channels", new_callable=AsyncMock
    ) as mock_join_channels:
        await fetcher._join_channel("test_channel")
        mock_join_channels.assert_called_once_with(["test_channel"])


@pytest.mark.asyncio
async def test_join_channel_failure(fetcher):
    with patch.object(
        fetcher,
        "join_channels",
        new_callable=AsyncMock,
        side_effect=TwitchIOException("Join failed"),
    ):
        fetcher._user_lists["test_channel"] = ViewerListFetchData()

        with pytest.raises(VLFetcherChannelJoinError):
            await fetcher._join_channel("test_channel")

        assert fetcher._user_lists["test_channel"].error is not None
        assert fetcher._user_lists["test_channel"].done is True


@pytest.mark.asyncio
async def test_wait_for_user_list(fetcher):
    fetcher._user_lists["test_channel"] = ViewerListFetchData(done=False)

    async def set_done():
        await asyncio.sleep(0.2)
        fetcher._user_lists["test_channel"].done = True

    asyncio.create_task(set_done())
    await fetcher._wait_for_user_list("test_channel")

    assert fetcher._user_lists["test_channel"].done is True


@pytest.mark.asyncio
async def test_process_channel_task(fetcher):
    fetcher._join_channel = AsyncMock()
    fetcher._wait_for_user_list = AsyncMock()

    await fetcher._process_channel_task("test_channel")

    fetcher._join_channel.assert_called_once_with("test_channel")
    fetcher._wait_for_user_list.assert_called_once_with("test_channel")


@pytest.mark.asyncio
async def test_fetch_viewer_list_for_channels(fetcher):
    channels = ["channel1", "channel2", "channel3", "channel4", "channel5"]
    fetcher._kick_off_listener_tasks = AsyncMock()

    result, elapsed = await fetcher.fetch_viewer_list_for_channels(channels)

    assert set(result.keys()) == set(channels)
    assert isinstance(result["channel1"], ViewerListFetchData)
    assert isinstance(result["channel2"], ViewerListFetchData)
    assert isinstance(result["channel3"], ViewerListFetchData)
    assert isinstance(result["channel4"], ViewerListFetchData)
    assert isinstance(result["channel5"], ViewerListFetchData)
    assert elapsed > 0


@pytest.mark.asyncio
async def test_fetch_viewer_list_for_channels_just_one(fetcher):
    channels = ["channel1"]
    fetcher._kick_off_listener_tasks = AsyncMock()

    result, elapsed = await fetcher.fetch_viewer_list_for_channels(channels)

    assert set(result.keys()) == set(channels)
    assert isinstance(result["channel1"], ViewerListFetchData)
    assert elapsed > 0


@pytest.mark.asyncio
async def test_fetch_viewer_list_for_channels_vs_mixed_case(fetcher):
    """This is a weird edge case I needed to guard against. For most flows in the server, login
    names are user case. Except when someone (me) enters a properly cased name into the smoke test
    and it sidechannels its way in. So, adding .lower() in a few places will help better protect
    internals. From me."""
    channels = ["TotallyLeGitUserNameTho"]
    fetcher._kick_off_listener_tasks = AsyncMock()

    result, elapsed = await fetcher.fetch_viewer_list_for_channels(channels)

    assert set(result.keys()) == set(c.lower() for c in channels)
    assert isinstance(result["totallylegitusernametho"], ViewerListFetchData)
    assert elapsed > 0
