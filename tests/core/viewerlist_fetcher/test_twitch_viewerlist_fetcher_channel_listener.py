# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from twitchio.errors import TwitchIOException

from server.core.viewerlist_fetcher import (
    ViewerListFetchData,
    VLFetcherChannelJoinError,
)
from server.core.viewerlist_fetcher.viewerlist_fetcher_channel_listener import (
    ViewerListFetcherChannelListener,
)


@pytest.fixture
def mock_client():
    with patch(
        "server.core.viewerlist_fetcher.viewerlist_fetcher_channel_listener.Client",
        autospec=True,
    ):
        client = ViewerListFetcherChannelListener("test_worker", "test_token")
        return client


@pytest.fixture
def fetcher():
    return ViewerListFetcherChannelListener(
        worker_id="test_worker", access_token="test_token"
    )


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
async def test_event_raw_data_part_message(fetcher):
    with patch.object(
        fetcher, "part_channels", new_callable=AsyncMock
    ) as mock_part_channels:

        channel = "test_channel"
        fetcher._user_lists = {channel: ViewerListFetchData()}
        message = f":tmi.twitch.tv 366 lurkerbot {channel} :End of /NAMES list"

        await fetcher.event_raw_data(message)

        mock_part_channels.assert_called_with(channel)


@pytest.mark.asyncio
async def test_join_channel_success(mock_client):
    mock_client.join_channels = AsyncMock()
    await mock_client._join_channel("test_channel")
    mock_client.join_channels.assert_called_once_with(["test_channel"])


@pytest.mark.asyncio
async def test_join_channel_failure(mock_client):
    mock_client.join_channels = AsyncMock(side_effect=TwitchIOException("Join failed"))
    mock_client._user_lists["test_channel"] = ViewerListFetchData()

    with pytest.raises(VLFetcherChannelJoinError):
        await mock_client._join_channel("test_channel")

    assert mock_client._user_lists["test_channel"].error is not None
    assert mock_client._user_lists["test_channel"].done is True


@pytest.mark.asyncio
async def test_wait_for_user_list(mock_client):
    mock_client._user_lists["test_channel"] = ViewerListFetchData(done=False)

    async def set_done():
        await asyncio.sleep(0.2)
        mock_client._user_lists["test_channel"].done = True

    asyncio.create_task(set_done())
    await mock_client._wait_for_user_list("test_channel")

    assert mock_client._user_lists["test_channel"].done is True


@pytest.mark.asyncio
async def test_process_channel_task(mock_client):
    mock_client._join_channel = AsyncMock()
    mock_client._wait_for_user_list = AsyncMock()

    await mock_client._process_channel_task("test_channel")

    mock_client._join_channel.assert_called_once_with("test_channel")
    mock_client._wait_for_user_list.assert_called_once_with("test_channel")


@pytest.mark.asyncio
async def test_fetch_viewer_list_for_channels(mock_client):
    channels = ["channel1", "channel2", "channel3", "channel4", "channel5"]
    mock_client._kick_off_listener_tasks = AsyncMock()

    result, elapsed = await mock_client.fetch_viewer_list_for_channels(channels)

    assert set(result.keys()) == set(channels)
    assert isinstance(result["channel1"], ViewerListFetchData)
    assert isinstance(result["channel2"], ViewerListFetchData)
    assert isinstance(result["channel3"], ViewerListFetchData)
    assert isinstance(result["channel4"], ViewerListFetchData)
    assert isinstance(result["channel5"], ViewerListFetchData)
    assert elapsed > 0
