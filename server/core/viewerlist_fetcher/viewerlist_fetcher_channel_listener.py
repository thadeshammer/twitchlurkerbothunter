"""
ViewerListFetcherChannelListener

RESPECT THE RATE LIMIT. (See below.)

Given a list of channel names, will asynchronously (asyncio) attempt to join them, parse the
user lists from the 353 messages, then part from each channel immediately upon receiving the 366,
ignoring all other messages. Once it's done, it will return a dict with channel_names mapped to
lists of login names from the viewerlist.

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

    Instantiate one ViewerListFetcherChannelListener per multiprocess instance of ViewerListFetcher.

    client = ViewerListFetcherChannelListener(worker_id, access_token)
    await client.connect()
    for user_lists in big_user_lists_collection_of_somekind:
        user_lists = fetch_viewer_list_for_channels(list_of_channels)
        do_things_with_user_lists(user_lists)
        await asyncio.sleep(respect_rate_limit)
    await client.close()

    Minding the rate limit, call fetch_viewer_list_for_channels() with a list of channel names. It
    will return a copy of its internal _user_list dict that it will freshly construct each time you
    call fetch_viewer_list_for_channels().

References:
    Clear explanation - https://discuss.dev.twitch.com/t/chatbot-and-353-user-message/44968/4
    RFC-1459 - https://www.rfc-editor.org/rfc/rfc1459
    Example Parser - https://dev.twitch.tv/docs/irc/example-parser/
"""

import asyncio
import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Optional, Set, Tuple

from twitchio import Client
from twitchio.errors import (
    AuthenticationError,
    HTTPException,
    InvalidContent,
    IRCCooldownError,
    TwitchIOException,
    Unauthorized,
)

logger = logging.getLogger(__name__)


# These correspond to RFC 1459 / IRC protocol
IRC_CHATTER_LIST_MSG = "353"
IRC_END_OF_NAMES_MSG = "366"


class VLFetcherError(Exception):
    pass


class VLFetcherChannelPartError(VLFetcherError):
    pass


class VLFetcherChannelJoinError(VLFetcherError):
    pass


@dataclass
class ViewerListFetchData:
    user_names: Set[str] = field(default_factory=set)
    done: bool = False
    start_time: float = field(default_factory=perf_counter)
    end_time: Optional[float] = None
    time_elapsed: Optional[float] = None
    error: Optional[Exception] = None

    def calculate_time_elapsed(self):
        if self.start_time is not None and self.end_time is not None:
            self.time_elapsed = self.end_time - self.start_time


class ViewerListFetcherChannelListener(Client):
    """Core code to process one or more given channels. For each channel given:
        - JOIN chat.
        - Listen and parse 'CHATTER LIST' messages as they arrive.
        - Listen for 'END OF NAMES' messages, PART from channel upon receipt.
        - Return the list of observed viewer names collected during this operation.

    TO USE:
        - Instantiate ONE ViewerListFetcherChannelListener per ViewerListFetcher worker process.
        - Pass channels in a list to fetch_viewer_list_for_channels() and await response, which will
          be:
            Tuple[dict[str, ViewerListFetchData], float]:
                - A dict mapping channel_name to ViewerListFetchData
                - The total time this call took to join, fetch, and part from all given channels, in
                  seconds.
    """

    def __init__(self, worker_id: str, access_token: str):
        """Initialize a ViewerListFetcher for a worker. Provide it with the ID of the worker that
        owns it and the currently live access token for init.

        Args:
            worker_id (str): _description_
            access_token (str): _description_

        Raises:
            TypeError: _description_
            TypeError: _description_
        """
        if not isinstance(worker_id, str):
            raise TypeError(f"worker_id is {type(worker_id)} but needs be a str.")
        if not isinstance(access_token, str):
            raise TypeError(f"access_token is {type(access_token)} but needs be a str.")

        self._worker_id = worker_id
        self._name = f"ViewerListFetcher_{worker_id}"
        self._access_token = access_token

        self._channels: list[str] = []
        self._user_lists: dict[str, ViewerListFetchData] = {}

        self._ready_event = asyncio.Event()

        super().__init__(token=self._access_token, initial_channels=[])

    async def event_ready(self):
        """TwitchIO Client class override. Treat as a private member."""
        await super().event_ready()
        logger.info(f"{self._name} is ready.")
        self._ready_event.set()

    async def event_raw_data(self, data: str):
        """TwitchIO Client class override. Treat as a private member.

        This is where the chatter list and end-of-chatter-list messages are listened for and
        responded to.
        """
        logger.debug("TwitchIO Chat Client raw data: {data}")  # the nuclear option

        if IRC_CHATTER_LIST_MSG in data:
            # The "353" will only appear in raw event data if at least one channel has been joined.
            # So, until fetch_viewer_list_for_channels() is called with a list of channels, this
            # code here under the if can't fire, and the self._user_lists reference won't blow us
            # up.

            # Extract the channel name and user list from the 353 message. Here's a sample:
            # ":user!user@user.tmi.twitch.tv 353 this_bot = #channel :jane jack jill"
            # We split on the colons
            # [0] = ""
            # [1] = the prefix including the 353 and the name of our bot here.
            # [2] = the space-separated user list
            parts = data.split(":")
            if len(parts) > 2:
                # msg_parts ['user!user@user.tmi.twitch.tv', '353', 'this_bot', '=', '#channel']
                msg_parts = parts[1].strip().split()
                channel_name = msg_parts[-1].lstrip("#")
                if channel_name not in self._user_lists:
                    raise VLFetcherError(
                        f"VLFetcher {self._worker_id} wrong channel error {channel_name}"
                    )

                user_list = set(parts[2].split())
                self._user_lists[channel_name].user_names.update(user_list)
                logger.info(
                    f"VLFetcher {self._worker_id} for {channel_name}: {list(user_list)}"
                )

        if IRC_END_OF_NAMES_MSG in data:
            # Part from the channel after receiving the 366 indicating end-of-353 messages.
            # We split as above, except this time [2] is the end of names message.
            parts = data.split(":")
            if len(parts) > 2:
                # message = ":tmi.twitch.tv 366 this_bot channel :End of /NAMES list"
                # parts == ['', 'tmi.twitch.tv 366 this_bot my_channel ', 'End of /NAMES list']
                # msg_parts == ['tmi.twitch.tv', '366', 'this_bot', 'channel']
                msg_parts = parts[1].strip().split()
                channel_name = msg_parts[-1].lstrip("#")

                end_of_names_msg = parts[2].split()
                logger.info(f"Parting from {channel_name} because {end_of_names_msg}")

            self._user_lists[channel_name].end_time = perf_counter()
            self._user_lists[channel_name].calculate_time_elapsed()
            self._user_lists[channel_name].done = True

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
                self._user_lists[channel_name].error = e
                raise VLFetcherChannelPartError() from e

    async def _join_channel(self, channel_name: str):
        if not self._ready_event.is_set():
            logger.debug("Need to wait for event_ready before joining.")
            await self._ready_event.wait()
        try:
            await self.join_channels([channel_name])
        except (
            HTTPException,
            InvalidContent,
            AuthenticationError,
            IRCCooldownError,
            TwitchIOException,
            Unauthorized,
        ) as e:
            self._user_lists[channel_name].error = e
            self._user_lists[channel_name].done = True
            raise VLFetcherChannelJoinError() from e

        logger.info(f"{self._name} joined {channel_name}")

    async def _wait_for_user_list(self, channel_name: str):
        logger.debug(f"Waiting for user list messages from {channel_name}")
        while not self._user_lists[channel_name].done:
            # These messages reportedly arrive in the order of whole seconds, so this may be too
            # aggressive.
            await asyncio.sleep(0.1)

    async def _process_channel_task(self, channel_name: str):
        await self._join_channel(channel_name)
        await self._wait_for_user_list(channel_name)

    async def _kick_off_listener_tasks(self, channels: list[str]):
        tasks = []
        for channel in channels:
            tasks.append(self._process_channel_task(channel))
        await asyncio.gather(*tasks)

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
                - The total time this call took to join, fetch, and part from all given channels, in
                  seconds.
        """
        if not all(isinstance(c, str) for c in channels):
            raise TypeError("channels list contains non-str type(s).")

        self._user_lists = {channel: ViewerListFetchData() for channel in channels}
        start_time: float = perf_counter()

        try:
            logger.debug("Kicking off listener tasks.")
            await self._kick_off_listener_tasks(channels)
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


# Sample usage follows
# TODO need to review this since the 366 refactor

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
