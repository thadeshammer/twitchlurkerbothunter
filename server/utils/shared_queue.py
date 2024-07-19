import asyncio
from multiprocessing import Lock as multi_proc_lock
from multiprocessing import Manager as multi_proc_manager
from typing import Any, Optional

import redis.asyncio as redis_async


class SharedQueueError(Exception):
    pass


class SharedQueueFull(Exception):
    pass


class SharedQueue:
    """Serves a queue that can be shared by multiprocess processes.

    This implementation uses Redis under the hood.
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
        self.item_count = 0
        self.size_limit: Optional[int] = size_limit

    async def queue_size(self) -> int:
        """Return the approximate size of the queue."""
        with self._process_lock:
            async with self._async_lock:
                try:
                    queue_size = await self.__db.llen(self.key)
                except Exception as e:
                    raise SharedQueueError("Failed to get queue size.") from e
                return queue_size

    async def enqueue(self, item: str) -> None:
        """Put item into the queue."""
        with self._process_lock:
            async with self._async_lock:
                if self.size_limit is not None and self.item_count == self.size_limit:
                    raise SharedQueueFull()
                try:
                    await self.__db.rpush(self.key, item)
                    self.item_count += 1
                except Exception as e:
                    raise SharedQueueError("Failed to enqueue.") from e

    async def dequeue(self, timeout: int = 2) -> Optional[str]:
        """Remove and return an item from the queue."""
        with self._process_lock:
            async with self._async_lock:
                if self.item_count < 0:
                    return None
                try:
                    # The docs type-hint blpop() as tuple[str, str] but it's actually
                    # tuple[bytes, bytes] at this time.
                    item: Optional[tuple[Any, Any]] = await self.__db.blpop(
                        self.key, timeout=timeout
                    )
                    if item is not None:
                        return_value = (
                            item[1].decode("utf-8")
                            if isinstance(item[1], bytes)
                            else item[1]
                        )
                    else:
                        return_value = None

                except Exception as e:
                    raise SharedQueueError("Failed to dequeue.") from e

                if return_value is not None:
                    self.item_count -= 1
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
                    raise SharedQueueError("Failed to clear queue.") from e
