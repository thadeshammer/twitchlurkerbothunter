# /server/core/viewerlist_fetcher/workbench.py
import asyncio
import logging
from time import perf_counter
from typing import Optional

from server.config import Config
from server.utils import (
    RedisSharedQueue,
    RedisSharedQueueDetails,
    get_redis_shared_queue,
)

logger = logging.getLogger(__name__)


class Workbench:
    def __init__(self):
        logger.debug("In Workbench __init__")
        self._redis_shared_queue_details_workbench = RedisSharedQueueDetails(
            name="workbench", size_limit=Config.TWITCH_CHANNEL_JOIN_LIMIT_COUNT
        )
        self._workbench_queue: RedisSharedQueue = get_redis_shared_queue(
            self._redis_shared_queue_details_workbench
        )

        self._redis_shared_queue_details_pending = RedisSharedQueueDetails(
            name="pending"
        )
        self._pending_queue: RedisSharedQueue = get_redis_shared_queue(
            self._redis_shared_queue_details_pending
        )

        # Fill the workbench HERE
        self._last_update_timemarker: float = perf_counter()
        self._ratelimit_timebox: float = float(
            Config.TWITCH_CHANNEL_JOIN_LIMIT_PER_SECONDS
        )

    def get_workbench_queue_details(self) -> RedisSharedQueueDetails:
        """Workers will use this to set up their own access to the workbench queue, connecting to
        the Redis instance directly.

        Returns:
            RedisSharedQueueDetails: Connection details to be used with RedisSharedQueue's
            get_redis_shared_queue factory method.
        """
        return self._redis_shared_queue_details_workbench

    def get_pending_queue_details(self) -> RedisSharedQueueDetails:
        """The StreamFetcher will need these details to connect to Redis to feed this queue there.

        Returns:
            RedisSharedQueueDetails: Connection details to be used with RedisSharedQueue's
            get_redis_shared_queue factory method.
        """
        return self._redis_shared_queue_details_pending

    async def update(self) -> bool:
        """Call this at a regular cadence to update the workbench queue from pending queue. Will
        return True if its internal rate limit timer tracking allowed an update; False otherwise.

        Returns:
            bool: True if its internal rate limit timer tracking allowed an update; False otherwise.
        """
        logger.debug("Updating workbench.")
        if self._ratelimit_timebox + self._last_update_timemarker >= perf_counter():
            logger.debug("Too soon for update.")
            return False

        pending_queue_size: int = await self._pending_queue.queue_size()
        space_on_workbench: Optional[int] = (
            await self._workbench_queue.remaining_space()
        )

        if pending_queue_size > 0:
            tasks = [self._pending_queue.dequeue() for _ in range(space_on_workbench)]
            results: list[tuple[Optional[str], Optional[dict[str, str]]]] = (
                await asyncio.gather(*tasks)
            )

            valid_items = [item[0] for item in results if item[0] is not None]

            if not valid_items:
                logger.info("Ran out of items in pending, nothing for the workbench.")

            enqueue_tasks = [
                self._workbench_queue.enqueue(item) for item in valid_items
            ]
            await asyncio.gather(*enqueue_tasks)

        return True
