# TODO file path and name
"""
    ScanConductor

    Reponsible for:

    - Creates a new ScanningSession table entry.
    - Oversee transfer of streams-to-scan from the StreamFetcher over to the StreamViewerList
      workbench.
    - Ensure the Rate Limit is respected.
    - Updates the ScanningSession with relevant metrics both during runtime and when complete.
    
"""
import logging

from server.utils import (
    RedisSharedQueue,
    RedisSharedQueueDetails,
    get_redis_shared_queue,
)

from .viewerlist_fetcher import ViewerListFetcher, Workbench

logger = logging.getLogger("__name__")


class ScanConductor:
    def __init__(self, access_token: str):
        self._access_token = access_token
        self._the_workbench: Workbench = Workbench()
        self.workbench_queue_details: RedisSharedQueueDetails = (
            self._the_workbench.get_workbench_queue_details()
        )
        self._workbench_queue: RedisSharedQueue = get_redis_shared_queue(
            self.workbench_queue_details
        )
        self._viewerlist_fetcher: ViewerListFetcher = ViewerListFetcher(
            "worker1", self._access_token, self.workbench_queue_details
        )

    async def try_it_out(self, channel_name: str):
        logger.debug(f"{self.workbench_queue_details=}")
        logger.debug(f"Starting test scan: {channel_name}")
        logger.debug("Enqueuing.")
        await self._workbench_queue.enqueue(channel_name)  # FOR TESTING
        logger.debug("Updating workbench next.")
        await self._the_workbench.update()
        logger.debug("Starting processing loop.")
        await self._viewerlist_fetcher.processing_loop()
