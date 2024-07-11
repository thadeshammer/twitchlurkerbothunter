# /app/helpers/shard_cache.py
"""
    ShardCache

    This is a sharded cache that creates `num_shards` shards and manages balancing distribution of
    data evenly across them with MD5 hashing. It uses multiprocessing.Manager.dict and Locks to work
    concurrently; it's also asyncio ready.

    TODO Needs testing beyond the unit tests I cobbled together.

    Example usage:

        # /app/main.py
        import asyncio
        from helpers.shard_cache import ShardCache

        async def worker(cache, worker_id):
            await cache.set(f"key{worker_id}", f"value{worker_id}")
            value = await cache.get(f"key{worker_id}")
            print(f"Worker {worker_id}: key{worker_id} = {value}")

        async def main():
            num_shards = 4
            cache = ShardCache(num_shards)

            # Create worker tasks
            tasks = [asyncio.create_task(worker(cache, i)) for i in range(10)]
            await asyncio.gather(*tasks)

        if __name__ == "__main__":
            asyncio.run(main())

"""
import hashlib
from multiprocessing import Lock, Manager
from multiprocessing.managers import DictProxy
from typing import Any


class ShardCache:
    def __init__(self, num_shards: int):
        self.num_shards: int = num_shards
        self.manager = Manager()
        self.shards: list[DictProxy[str, Any]] = [
            self.manager.dict() for _ in range(num_shards)
        ]
        self.locks = [Lock() for _ in range(num_shards)]

    def _get_shard_index(self, key: str) -> int:
        """MD5 hashing is used to evenly distribute keys across the number of shards.

        Args:
            key (str): The key for the data that's held in the cache.

        Returns:
            int: The list index of the specific dict within the cache, which is a list.
        """
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.num_shards

    async def set(self, key: str, value: Any) -> None:
        """Create or update cached data at the given key; will handle finding the appropriate shard.

        Args:
            key (str): The key associated with the data.
            value (Any): Whatever object you want stored.
        """
        shard_index = self._get_shard_index(key)
        with self.locks[shard_index]:
            self.shards[shard_index][key] = value

    async def get(self, key: str) -> Any | None:
        """Fetch data from the cache; handles finding the appropriate shard.

        Args:
            key (str): The key associated with the data.

        Returns:
            Any: Data from the cache, or None if the key isn't in the cache.
        """
        shard_index = self._get_shard_index(key)
        with self.locks[shard_index]:
            return self.shards[shard_index].get(key)

    async def delete(self, key: str) -> None:
        """Delete data currently in the cache; handles finding the appropriate shard.

        Args:
            key (str): The key associated with the data.
        """
        shard_index = self._get_shard_index(key)
        with self.locks[shard_index]:
            if key in self.shards[shard_index]:
                del self.shards[shard_index][key]
