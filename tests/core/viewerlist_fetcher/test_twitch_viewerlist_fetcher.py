# pylint: disable=protected-access

from unittest.mock import AsyncMock, patch

import pytest

from server.core.twitch_viewerlist_fetcher import (
    TwitchViewerListFetcher,
    ViewerListFetchData,
)


@pytest.fixture
def _fetcher():
    return TwitchViewerListFetcher(worker_id="test_worker", access_token="test_token")


@pytest.mark.asyncio
async def test_event_raw_data_chatter_list_message(_fetcher):
    _fetcher._user_lists = {"test_channel": ViewerListFetchData()}
    message = ":tmi.twitch.tv 353 this_bot = #test_channel :user1 user2 user3"

    await _fetcher.event_raw_data(message)

    assert _fetcher._user_lists["test_channel"].user_names == {
        "user1",
        "user2",
        "user3",
    }


@pytest.mark.asyncio
async def test_event_raw_data_chatter_list_message_no_names(_fetcher):
    _fetcher._user_lists = {"test_channel": ViewerListFetchData()}
    message = ":tmi.twitch.tv 353 this_bot = #test_channel :"

    await _fetcher.event_raw_data(message)

    assert len(_fetcher._user_lists["test_channel"].user_names) == 0


@pytest.mark.asyncio
async def test_event_raw_data_part_message(_fetcher):
    with patch.object(
        _fetcher, "part_channels", new_callable=AsyncMock
    ) as mock_part_channels:

        channel = "test_channel"
        _fetcher._user_lists = {channel: ViewerListFetchData()}
        message = f":tmi.twitch.tv 366 lurkerbot {channel} :End of /NAMES list"

        await _fetcher.event_raw_data(message)

        mock_part_channels.assert_called_with(channel)


@pytest.mark.asyncio
@patch(
    "server.core.twitch_viewerlist_fetcher.perf_counter",
    return_value=0.0,
)
@patch("server.core.twitch_viewerlist_fetcher.logger")
@patch.object(TwitchViewerListFetcher, "join_channels", new_callable=AsyncMock)
@patch.object(TwitchViewerListFetcher, "_wait_for_all_users", new_callable=AsyncMock)
async def test_fetch_viewer_list_for_channels(
    mock_wait_for_all_users,
    mock_join_channels,
    mock_logger,
    mock_perf_counter,
    _fetcher,
):  # pylint: disable=unused-argument
    channels = ["test_channel1", "test_channel2"]
    _fetcher._user_lists = {channel: ViewerListFetchData() for channel in channels}

    result, _ = await _fetcher.fetch_viewer_list_for_channels(channels)

    mock_join_channels.assert_called_with(*channels)
    mock_wait_for_all_users.assert_called_with(channels)
    assert result == _fetcher._user_lists.copy()


@pytest.mark.asyncio
async def test_wait_for_all_users(_fetcher):
    with patch("asyncio.sleep", new_callable=AsyncMock):
        _fetcher._user_lists = {"test_channel": ["user1"]}
        await _fetcher._wait_for_all_users(["test_channel"])
        # No assertions needed, just ensure it completes without errors
