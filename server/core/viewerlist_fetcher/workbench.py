# /server/core/viewerlist_fetcher/workbench.py
import asyncio
import logging
from time import perf_counter
from typing import Optional

from server.config import Config
from server.utils import (
    RedisSharedQueue,
    RedisSharedQueueDetails,
    RedisSharedQueueError,
    RedisSharedQueueFull,
    get_redis_shared_queue,
)

logger = logging.getLogger(__name__)


class Workbench:
    def __init__(self):
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
        self._stopwatch: float = perf_counter()
        self._timebox: float = float(Config.TWITCH_CHANNEL_JOIN_LIMIT_PER_SECONDS)

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

    async def update(self):
        # Every ten seconds, fill the workbench queue up to max fill (20 for now) from pending
        # Keep track of the timer
        current_time = perf_counter()
        if current_time >= self._stopwatch + self._timebox:
            # reset stopwatch
            self._stopwatch = current_time

            space_on_workbench, pending_queue_size = await asyncio.gather(
                self._workbench_queue.remaining_space(),
                self._pending_queue.queue_size(),
            )

            # enqueue up to space_on_workbench from pending_queue
            if pending_queue_size > 0:
                for _ in range(space_on_workbench):
                    item: tuple[Optional[str], Optional[dict[str, str]]] = (
                        await self._pending_queue.dequeue()
                    )
                    if item[0] is None:
                        logger.info(
                            "Ran out of items in pending, nothing for the workbench."
                        )
                        break  # we're done, we need to park or wait or something.
                    await self._workbench_queue.enqueue(item[0])
