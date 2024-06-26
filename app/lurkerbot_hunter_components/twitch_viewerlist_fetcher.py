import asyncio
import logging

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


class TwitchViewerListFetcher(Client):

    def __init__(self, worker_id: str, access_token: str):
        self._worker_id = worker_id
        self._name = f"ViewerListFetcher_{worker_id}"
        self._access_token = access_token

        self._channels: list[str] = []
        self._user_lists: dict[str, list[str]] = {}

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
                self._user_lists[channel_name].extend(user_list)
                logger.info(
                    f"User list for {channel_name}: {self._user_lists[channel_name]}"
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

    async def fetch_viewer_list_for_channels(
        self, channels: list[str]
    ) -> dict[str, list[str]]:
        self._user_lists = {channel: [] for channel in channels}

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

        return self._user_lists.copy()

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
