"""
TwitchViewerListFetcher

RESPECT THE RATE LIMIT. (See below.)

Given a list of channel names, will asynchronously (asyncio) attempt to join them, parse the
user lists from the 353 message, then part from each channel immediately. Once it's done, it
will return a dict with channel_names mapped to lists of login names from the viewerlist.

This class uses TwitchIO to handle the noodly parts of interfacing with Twitch's IRC.

Usage:
    NOTE. RESPECT THE RATE LIMIT. The rate limit for unapproved bots (like me) is a max of 20
    channel joins per 10 second window, per the docs. You'll need to manage this outside of this
    class. The reason being 1. single responsiblity and 2. the use case we're desiging for is using
    this across multiple process workers which will all go faster but must together respect the rate
    limit.

    The plan is for the conductor to handle this: it will refill a queue to size 20 with unchecked
    streams every 10 seconds, so that if we go to slow, len(queue) <= 20, and if we go too fast, the
    queue will bounce from 0 to 20 at the 10s mark, such that we can't possibly exceed the rate.

    Instantiate one TwitchViewerListFetcher per multiprocess instance or microservice.

    client = TwitchViewerListFetcher(worker_id, access_token)
    await client.connect()
    for user_lists in big_user_lists_collection_of_somekind:
        user_lists = fetch_viewer_list_for_channels(list_of_channels)
        do_things_with_user_lists(user_lists)
        await asyncio.sleep(respect_rate_limit)
    await client.close()

    Minding the rate limit, call fetch_viewer_list_for_channels() with a list of channel names. It
    will return a copy of its internal _user_list dict that it will freshly construct each time you
    call fetch_viewer_list_for_channels().
"""

import asyncio
import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Optional, Tuple

from twitchio import Client
from twitchio.errors import (
    AuthenticationError,
    HTTPException,
    InvalidContent,
    IRCCooldownError,
    TwitchIOException,
    Unauthorized,
)

logger = logging.getLogger("app")


@dataclass
class ViewerListFetchData:
    user_names: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=perf_counter)
    end_time: Optional[float] = None
    time_elapsed: Optional[float] = None

    def calculate_time_elapsed(self):
        if self.start_time is not None and self.end_time is not None:
            self.time_elapsed = self.end_time - self.start_time


class TwitchViewerListFetcher(Client):

    def __init__(self, worker_id: str, access_token: str):
        assert isinstance(worker_id, str) and isinstance(access_token, str)

        self._worker_id = worker_id
        self._name = f"ViewerListFetcher_{worker_id}"
        self._access_token = access_token

        self._channels: list[str] = []
        self._user_lists: dict[str, ViewerListFetchData] = {}

        super().__init__(token=self._access_token, initial_channels=[])

    async def event_ready(self):
        logger.info(f"{self._name} is ready.")

    async def event_raw_data(self, data: str):
        if "353" in data:
            # The "353" will only appear in raw event data if at least one channel has been joined.
            # So, until fetch_viewer_list_for_channels() is called with a list of channels, this
            # code here under the if can't fire, and the self._user_lists reference won't blow us
            # up.

            # Extract the channel name and user list from the 353 message. Here's a sample:
            # ":user!user@user.tmi.twitch.tv 353 this_bot = #test_channel :user1 user2 user3"
            # We split on the colons
            # [0] = ""
            # [1] = the prefix including the 353 and the name of our bot here.
            # [2] = the space-separated user list
            parts = data.split(":")
            if len(parts) > 2:
                # msg_parts ['user!user@user.tmi.twitch.tv', '353', 'this_bot', '=', '#test_channel']
                msg_parts = parts[1].strip().split()
                channel_name = msg_parts[-1]
                user_list = parts[2].split()
                self._user_lists[channel_name].user_names.extend(user_list)
                logger.info(
                    f"User list for {channel_name}: {self._user_lists[channel_name].user_names}"
                )

                # Part from the channel after receiving the user list
                try:
                    await self.part_channels(channel_name)
                except (
                    HTTPException,
                    InvalidContent,
                    AuthenticationError,
                    IRCCooldownError,
                    TwitchIOException,
                    Unauthorized,
                ) as e:
                    logger.error(f"Error fetching viewer list for channels: {e}")
                    raise e

                self._user_lists[channel_name].end_time = perf_counter()
                self._user_lists[channel_name].calculate_time_elapsed()

    async def fetch_viewer_list_for_channels(
        self, channels: list[str]
    ) -> Tuple[dict[str, ViewerListFetchData], float]:
        """Given a list of channel names, fetches each of their viewer lists.

        Args:
            channels (list[str]): A list of channels to fetch viewer-lists from.

        Raises:
            e: Most of the possible TwitchIO errors.

        Returns:
            Tuple[dict[str, ViewerListFetchData], float]:
                - A dict mapping channel_name to ViewerListFetchData
                - The time this call took to join, fetch, and part from all given channels, in
                  seconds.
        """
        assert isinstance(channels, list[str])
        self._user_lists = {channel: ViewerListFetchData() for channel in channels}
        start_time: float = perf_counter()

        try:
            await self.join_channels(*channels)
            logger.info(f"{self._name} joined {channels}")
            await self._wait_for_all_users(channels)
        except (
            HTTPException,
            InvalidContent,
            AuthenticationError,
            IRCCooldownError,
            TwitchIOException,
            Unauthorized,
        ) as e:
            logger.error(f"Error fetching viewer list for channels: {e}")
            raise e

        total_time_elapsed = perf_counter() - start_time
        return self._user_lists.copy(), total_time_elapsed

    async def _wait_for_all_users(self, channels: list[str]) -> None:
        while any(channel not in self._user_lists for channel in channels):
            await asyncio.sleep(0.1)


# Sample usage follows

# async def process_batches(client, batches):
#     for batch in batches:
#         print(f'Processing batch: {batch}')
#         user_lists = await client.fetch_viewer_list_for_channels(batch)
#         print(f'User lists: {user_lists}')
#         await asyncio.sleep(10)  # Respect the rate limit

# async def main():
#     token = 'YOUR_IRC_TOKEN'
#     channels = ['channel1', 'channel2', 'channel3']  # Example initial channels
#     client = TwitchClient(token, channels)

#     # Example batches of channels to process
#     batches = [
#         ['channel1', 'channel2', 'channel3'],
#         ['channel4', 'channel5', 'channel6'],
#         ['channel7', 'channel8', 'channel9'],
#         # Add more batches as needed
#     ]

#     await client.connect()
#     await process_batches(client, batches)
#     await client.close()

# if __name__ == "__main__":
#     asyncio.run(main())
