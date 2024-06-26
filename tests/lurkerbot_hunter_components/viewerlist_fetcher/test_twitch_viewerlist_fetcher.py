# pylint: disable=protected-access

from unittest.mock import AsyncMock, patch

import pytest

from app.lurkerbot_hunter_components.twitch_viewerlist_fetcher import (
    TwitchViewerListFetcher,
)


@pytest.fixture
def _fetcher():
    return TwitchViewerListFetcher(worker_id="test_worker", access_token="test_token")


@pytest.mark.asyncio
async def test_event_ready(_fetcher):
    with patch(
        "app.lurkerbot_hunter_components.twitch_viewerlist_fetcher.logger"
    ) as mock_logger:
        await _fetcher.event_ready()
        mock_logger.info.assert_called_with("ViewerListFetcher_test_worker is ready.")


@pytest.mark.asyncio
async def test_event_raw_data(_fetcher):
    with patch(
        "app.lurkerbot_hunter_components.twitch_viewerlist_fetcher.logger"
    ) as mock_logger, patch.object(
        _fetcher, "part_channels", new_callable=AsyncMock
    ) as mock_part_channels:

        _fetcher._user_lists = {"#test_channel": []}
        data = ":user!user@user.tmi.twitch.tv 353 this_bot = #test_channel :user1 user2 user3"

        await _fetcher.event_raw_data(data)

        mock_part_channels.assert_called_with("#test_channel")
        mock_logger.info.assert_called_with(
            "User list for #test_channel: ['user1', 'user2', 'user3']"
        )


@pytest.mark.asyncio
async def test_fetch_viewer_list_for_channels(_fetcher):
    with patch(
        "app.lurkerbot_hunter_components.twitch_viewerlist_fetcher.logger"
    ) as mock_logger, patch.object(
        _fetcher, "join_channels", new_callable=AsyncMock
    ) as mock_join_channels, patch.object(
        _fetcher, "_wait_for_all_users", new_callable=AsyncMock
    ) as mock_wait_for_all_users:

        channels = ["#test_channel1", "#test_channel2"]
        _fetcher._user_lists = {channel: [] for channel in channels}

        result = await _fetcher.fetch_viewer_list_for_channels(channels)

        mock_join_channels.assert_called_with(*channels)
        mock_wait_for_all_users.assert_called_with(channels)
        assert result == _fetcher._user_lists.copy()
        mock_logger.info.assert_any_call(
            f"ViewerListFetcher_test_worker joined {channels}"
        )


@pytest.mark.asyncio
async def test_wait_for_all_users(_fetcher):
    with patch("asyncio.sleep", new_callable=AsyncMock):
        _fetcher._user_lists = {"#test_channel": ["user1"]}
        await _fetcher._wait_for_all_users(["#test_channel"])
        # No assertions needed, just ensure it completes without errors
