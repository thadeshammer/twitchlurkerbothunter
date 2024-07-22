# server/utils/redis_shared_queue.py
"""
    RedisSharedQueue

    A queue that's hosted in Redis so that all mutable data is handled safely for multiprocess
    stuff.

    Usage:
        - fill out a RedisSharedQueueDetails structure, fill out name at a minimum
            - optionally provide size_limit when desired
        - call get_redis_shared_queue(deets: RedisSharedQueueDetails) to get your queue wrapper

        - ONLY ONE MULTIPROCESS SHOULD HOLD RESPONSIBLITY FOR ENQUEUEING. Enqueue is a lock
          bottleneck by design to make size_limiting easier for now. (The goal is to respect
          Twitch's rate limit.)
        - Dequeue as you like.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from multiprocessing import Lock as multi_proc_lock
from multiprocessing import Manager as multi_proc_manager
from typing import Any, Optional, Union

import redis.asyncio as redis_async
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import InvalidResponse as RedisInvalidResponse
from redis.exceptions import RedisError
from redis.exceptions import ResponseError as RedisResponseError
from redis.exceptions import TimeoutError as RedisTimeoutError

from server.config import Config

logger = logging.getLogger(__name__)


class RedisSharedQueueError(Exception):
    pass


class RedisSharedQueueFull(Exception):
    pass


@dataclass
class RedisSharedQueueDetails:
    """Collected config details to access a specific shared queue in a Redis instance.

    REQUIRED:
        - `name` of the queue

    OPTIONAL:
        - size_limit (int): Max number of items allowed in the queue at once; enqueuing beyond this
          will raise a RedisSharedQueueFull Exception.
        - namespace (str): "queue" by default,  The Redis key = f"{namespace}:{name} and you can
          override the namespace if desired.
        - redis_args (dict[str, str]): host, port, db_index, defaults to Config
    """

    name: str
    size_limit: Optional[int] = None
    namespace: str = "queue"
    redis_args: dict[str, str] = field(default_factory=Config.get_redis_args)


def get_redis_shared_queue(
    details: RedisSharedQueueDetails,
) -> "RedisSharedQueue":
    """Use THIS builder function for each process that will be sharing the queue. DO NOT SHARE A
    SHAREDQUEUE single reference across multiple processes or you will run into thread starvation.
    We're using Redis specifically to offload fair locking mechanisms from our app here.

    Raises:
        SharedQueueError: If connection to Redis fails.

    Returns:
        RedisSharedQueue wrapping a list in the Redis instance.
    """
    try:
        return RedisSharedQueue(
            details.name, details.size_limit, details.namespace, **details.redis_args
        )
    except (
        RedisError,
        RedisTimeoutError,
        RedisResponseError,
        RedisConnectionError,
        RedisInvalidResponse,
    ) as e:
        logger.error(f"Failed to create SharedQueue. {e=}")
        raise RedisSharedQueueError from e


class RedisSharedQueue:
    """USE THE BUILDER FUNCTION `get_shared_queue()`. I.D. QUEUE WITH NAMESPACE:NAME AS KEY.

    Serves a queue that (in theory) can be shared by multiprocess processes which each use asyncio.

    USAGE. Leverage the fact that this implementation uses Redis under the hood. Share the details
    used to instantiate this SharedQueue and not the SharedQueue reference itself: create multiple,
    independent instances of SharedQueue all connecting to the same Redis instance and Redis key and
    let Redis worry about thread-safety.

    enqueue: If you set a size_limit, this method will raise a RedisSharedQueueFull error if it's
    full. It uses a Redis lua script to enforce the size limit, and it uses an asyncio lock and
    multiprocess lock to make sure race conditions bypassing the size limit are impossible. (Redis
    should alone handle this, but the word *should* wound up with me locking this critical code.)

    dequeue: It's not locked down at all and multiple workers may get to the pop call and only some
    of  them will get items; others will come up empty (with None). You can set a timeout if you
    want the worker to park for some number of seconds until a new item is available.

    NOTE. It turns out that asyncio and multiprocess don't play nicely together in terms of shared
    memory which is why we're using Redis; however it turns out, using multiprocess locks will
    deadlock the asyncio event loop. Seems if we acquire an asyncio lock (for the given
    multiprocess) first, we're okay...but I haven't tested extensively with multiprocess yet, so we
    may need to fall back on Redis 100% here until I can learn more about how to make these two
    thing mingle in Python town.
    """

    _manager = multi_proc_manager()

    def __init__(
        self,
        name: str,
        namespace: str = "queue",
        size_limit: Optional[int] = None,
        **redis_kwargs,
    ):
        self.__db = redis_async.Redis(**redis_kwargs)
        self.key = f"{namespace}:{name}"
        self._multiprocess_lock: multi_proc_lock = self._manager.Lock()
        self._asyncio_lock = asyncio.Lock()
        self.size_limit: Optional[int] = size_limit

        # Lua script to check size limit and enqueue atomically
        self.size_limit_script = f"""
        local key = KEYS[1]
        local size_limit = tonumber({self.size_limit})
        local item = ARGV[1]
        local current_size = redis.call('LLEN', key)
        if current_size < size_limit then
            redis.call('RPUSH', key, item)
            return 1
        else
            return 0
        end
        """

        # Lua script when there's no resize but still enforces atomicity.
        self.no_size_limit_script = """
        local key = KEYS[1]
        local item = ARGV[1]
        redis.call('RPUSH', key, item)
        return 1
        """

        self._enqueue_with_limit = self.__db.register_script(self.size_limit_script)
        self._enqueue_without_limit = self.__db.register_script(
            self.no_size_limit_script
        )

        if self.size_limit is not None:
            self._enqueue = self._enqueue_with_limit
        else:
            self._enqueue = self._enqueue_without_limit

        # Lua script for dequeue
        self.dequeue_script = """
        local key = KEYS[1]
        local timeout = tonumber(ARGV[1])
        local item = redis.call('BLPOP', key, timeout)
        if item then
            return item[2]
        else
            return nil
        end
        """
        self._dequeue_script = self.__db.register_script(self.dequeue_script)

        # Lua script for clear
        self.clear_script = """
        local key = KEYS[1]
        local keys = redis.call('KEYS', key .. '*')
        if #keys > 0 then
            return redis.call('DEL', unpack(keys))
        else
            return 0
        end
        """
        self._clear_script = self.__db.register_script(self.clear_script)

    async def queue_size(self) -> int:
        try:
            queue_size = await self.__db.llen(self.key)
        except Exception as e:
            raise RedisSharedQueueError("Failed to get queue size.") from e
        return queue_size

    async def remaining_space(self) -> Optional[int]:
        if self.size_limit is None:
            return None
        return self.size_limit - (await self.queue_size())

    async def enqueue(self, item: Union[str, dict[str, str]]) -> None:
        """Put item into the queue. ONLY ONE PROCESS SHOULD BE TRUSTED TO ENQUEUE IF A LIMIT IS IN
        PLACE. Otherwise a resulting race condition between enqueueing processes will breeze past
        the size_limit check and blow past the limit. If there is no limit, it's probably fine to
        bypass acquiring the process lock, but for now it's uniform for this method.

        NOTE. Using atomic Lua scripts _should_ mitigate this and obviate the need for the locking
        approach I initialized used here; worth testing.

        Args:
            item (str, dict[str, str]): The value to put at the end of the queue. Can be a
            dict[str, str] which will be json-ified into Redis as a string.

        Raises:
            RedisSharedQueueFull: If this enqueue action would break the size_limit, the value will
            not be enqueued and will be discarded here. The caller is responsible to hold and
            resubmit.

            RedisSharedQueueError: If the Redis.rpush fails, this is raised.
        """
        async with self._asyncio_lock:
            with self._multiprocess_lock:
                if isinstance(item, dict):
                    data: str = json.dumps(item)
                else:
                    data = str(item)
                try:
                    result = await self._enqueue(keys=[self.key], args=[data])
                    if result == 0:
                        if self.size_limit is not None:
                            raise RedisSharedQueueFull()
                        raise RedisSharedQueueError(
                            "No size limit set but enqueue blocked by size limit script."
                        )
                except (
                    RedisConnectionError,
                    RedisError,
                    RedisInvalidResponse,
                    RedisResponseError,
                    RedisTimeoutError,
                ) as e:
                    raise RedisSharedQueueError("Failed to enqueue.") from e

    async def dequeue(
        self, timeout: int = 2
    ) -> tuple[Optional[str], Optional[dict[str, str]]]:
        """Remove and return an item from the queue.

        NOTE. asyncio_lock only, meaning two or more workers may get past the `queue_size` check and
        when one succeeds at getting the final element, the others will come back and return None.
        In short, racing is allowed here as it should be harmless.

        Args:
            timeout (int, optional): Seconds to park and wait for Redis. Defaults to 2.

        Raises:
            RedisSharedQueueError: If Redis blpop fails, this is raised.

        Returns:
            Tuple(Optional[str], Optional[dict]):
                The next value in the queue as a raw string and parsed json dict if applicable.
                If the queue is empty, return (None, {})
        """
        if (await self.queue_size()) == 0:
            return (None, {})
        try:
            item: Optional[str] = await self._dequeue_script(
                keys=[self.key], args=[timeout]
            )
            if item is None:
                return_value = (None, {})
            else:
                raw_data: str = (
                    item.decode("utf-8") if isinstance(item, bytes) else item
                )
                try:
                    json_data: dict[str, str] = json.loads(raw_data)
                except json.JSONDecodeError:
                    json_data = {}
                return_value = (raw_data, json_data)
        except (
            RedisConnectionError,
            RedisError,
            RedisInvalidResponse,
            RedisResponseError,
            RedisTimeoutError,
        ) as e:
            raise RedisSharedQueueError("Failed to dequeue.") from e
        return return_value

    async def empty(self) -> bool:
        return (await self.queue_size()) == 0

    async def clear(self) -> None:
        await self._clear_script(keys=[self.key])
