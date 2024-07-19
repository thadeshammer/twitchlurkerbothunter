import asyncio
import logging
from dataclasses import dataclass, field
from multiprocessing import Lock as multi_proc_lock
from multiprocessing import Manager as multi_proc_manager
from typing import Any, Optional

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
) -> Optional["RedisSharedQueue"]:
    """Use THIS builder function for each process that will be sharing the queue. DO NOT SHARE A
    SHAREDQUEUE single reference across multiple processes or you will run into thread starvation.
    We're using Redis specifically to offload fair locking mechanisms from our app here.

    Raises:
        SharedQueueError: _description_

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

    Serves a queue that can be shared by multiprocess processes. Does nothing intrinsically to
    guard against process starvation.

    USAGE. Leverage the fact that this implementation uses Redis under the hood. Share the details
    used to instantiate this SharedQueue and not the SharedQueue reference itself: create multiple,
    independent instances of SharedQueue all connecting to the same Redis instance and Redis key and
    let Redis worry about thread-safety.
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
        self._process_lock: multi_proc_lock = self._manager.Lock()
        self._async_lock = asyncio.Lock()
        self.size_limit: Optional[int] = size_limit

    async def queue_size(self) -> int:
        """Return the approximate size of the queue."""
        try:
            queue_size = await self.__db.llen(self.key)
        except Exception as e:
            raise RedisSharedQueueError("Failed to get queue size.") from e
        return queue_size

    async def enqueue(self, item: str) -> None:
        """Put item into the queue. ONLY ONE PROCESS SHOULD BE TRUSTED TO ENQUEUE IF A LIMIT IS IN
        PLACE. Otherwise a resulting race condition between enqueueing processes will breeze past
        the size_limit check and blow past the limit. If there is no limit, it's probably fine to
        bypass acquiring the process lock, but for now it's uniform for this method.

        Args:
            item (str): The value to put at the end of the queue.

        Raises:
            RedisSharedQueueFull: If this enqueue action would break the size_limit, the value will
            not be enqueued and will be discarded here. The caller is responsible to hold and
            resubmit.

            RedisSharedQueueError: If the Redis.rpush fails, this is raised.
        """
        with self._process_lock:
            async with self._async_lock:
                if self.size_limit is not None:
                    current_size = await self.queue_size()
                    if current_size == self.size_limit:
                        raise RedisSharedQueueFull()
                try:
                    await self.__db.rpush(self.key, item)
                except Exception as e:
                    raise RedisSharedQueueError("Failed to enqueue.") from e

    async def dequeue(self, timeout: int = 2) -> Optional[str]:
        """Remove and return an item from the queue.

        NOTE. asyncio_lock only, meaning two or more workers may get past the `queue_size` check and
        when one succeeds at getting the final element, the others will come back and return None.
        In short, racing is allowed here as it should be harmless.

        Args:
            timeout (int, optional): Seconds to park and wait for Redis. Defaults to 2.

        Raises:
            RedisSharedQueueError: If Redis blpop fails, this is raised.

        Returns:
            Optional[str]: The next value in the queue, or None if it's empty.
        """
        if (await self.queue_size()) == 0:
            return None
        try:
            # The docs type-hint blpop() as tuple[str, str] but it's actually
            # tuple[bytes, bytes] at this time.
            item: Optional[tuple[Any, Any]] = await self.__db.blpop(
                self.key, timeout=timeout
            )
            if item is not None:
                return_value = (
                    item[1].decode("utf-8") if isinstance(item[1], bytes) else item[1]
                )
            else:
                return_value = None

        except Exception as e:
            raise RedisSharedQueueError("Failed to dequeue.") from e

        if return_value is not None:
            return return_value

    async def empty(self) -> bool:
        """Return True if the queue is empty, False otherwise."""
        return (await self.queue_size()) == 0

    async def clear(self):
        with self._process_lock:
            async with self._async_lock:
                try:
                    await self.__db.delete(self.key)
                except Exception as e:
                    raise RedisSharedQueueError("Failed to clear queue.") from e
