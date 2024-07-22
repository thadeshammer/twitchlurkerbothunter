# server/core/viewerlist_fetcher/viewerlist_fetcher.py
"""
    ViewerListFetcher a.k.a. "the worker" or "line cook"

    The single responsibilty of this component is to fetch a viewerlist from a target stream within
    the rate limit. 

    Usage:
        - Spin this off in a Python multiprocess process with access to a Workbench Queue that is
          filled up to (and helps guard against breaking) the rate limit.
    Set-up:
        - Instantiate a single (ONLY ONE) ViewerlistFetcherChannelListener per ViewerListFetcher.
    Procedure:
        - Select TARGET_STREAM with TARGET_STREAM_DATA from Workbench queue. (If none, wait.)
            - This will be the 'Get Stream' dict.
            - https://dev.twitch.tv/docs/api/reference/#get-streams
        - Create a new partial TwitchUserData row for the streamer OR update existing.
        - Create a new StreamCategory row if necessary.
        - Create a new StreamViewerListFetch for TARGET_STREAM with TARGET_STREAM_DATA.
        - Kick off the ViewerlistFetcherChannelListener for TARGET_STREAM and await response.
        - Create ViewerSightings for each login name in that response.
        - Repeat.
    
    RATE LIMITING
    
    Configurable hard limits on quantity of chat-joins per window. Docs say it's 20 joins per 10s.
    We could play very safely and cap at 18 joins per 10s OR 20 joins per 10.2s, etc.
"""
import logging

from server.models import (
    StreamCategoryCreate,
    StreamViewerListFetchCreate,
    TwitchUserDataCreate,
)
from server.utils import (
    RedisSharedQueue,
    RedisSharedQueueDetails,
    get_redis_shared_queue,
)

from .viewerlist_fetcher_channel_listener import ViewerListFetcherChannelListener

logger = logging.getLogger("__name__")


class ViewerListFetcher:
    def __init__(
        self,
        worker_id: str,
        access_token: str,
        workbench_details: RedisSharedQueueDetails,
    ):

        self._worker_id = worker_id
        self._access_token = access_token
        self._workbench: RedisSharedQueue = get_redis_shared_queue(workbench_details)
        self._listener: ViewerListFetcherChannelListener = (
            ViewerListFetcherChannelListener(worker_id, access_token)
        )
        self._working = True
        self._idle = False

    def set_state(self, working_state: bool) -> bool:
        """Sets working_state, determining whether the process loop will keep looping.

        Args:
            working_state (bool): The state to set it to.

        Returns:
            bool: _description_
        """
        self._working = working_state
        return self._working

    def get_state(self) -> bool:
        return self._working

    async def processing_loop(self) -> None:
        while self._working:
            # one at a time for now
            target_channel, _ = await self._workbench.dequeue()
            if target_channel is None:
                self._working = False
                logger.info("Nothing on workbench.")
            else:
                logger.debug(f"Grabbed {target_channel} from workbench.")
                await self._listener.connect()
                results = await self._listener.fetch_viewer_list_for_channels(
                    [target_channel]
                )
                logger.info(f"{self._worker_id} GOT ONE: {results}")
        await self._listener.close()
