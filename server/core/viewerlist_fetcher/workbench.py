# /server/core/viewerlist_fetcher/workbench.py
from time import perf_counter
from typing import Any, Coroutine, Optional

from server.config import Config
from server.utils import (
    RedisSharedQueue,
    RedisSharedQueueDetails,
    RedisSharedQueueError,
    RedisSharedQueueFull,
    get_redis_shared_queue,
)


class Workbench:
    def __init__(self):
        self._redis_shared_queue_details = RedisSharedQueueDetails(
            name="workbench", size_limit=Config.TWITCH_CHANNEL_JOIN_LIMIT_COUNT
        )
        self._redis_shared_queue_details = RedisSharedQueueDetails(name="pending")
        self._redis_shared_queue = get_redis_shared_queue(
            self._redis_shared_queue_details
        )
