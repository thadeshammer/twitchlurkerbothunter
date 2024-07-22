"""
    ViewerSightingsCache

    Shared mutable temporary datastore for Viewerlist Fetcher Channel Listener Workers, aka
    "Listeners".

    Every worker (in-app multiprocess or external microservice) that connects to the same Redis
    instance, USES THE SAME NUM_SHARDS, and uses this class's built-in hashing will use the same
    cache/shards.

    USAGE: For each worker:
        - Use same configuration (num_shards and Redis connection args)
        - Call set_user_data for each name; collisions will update and increment times_seen.
        - Use clear_cache between scans or after unrecoverable errors
        - TO UPDATE FLAGS: Use set_aggregate and set_enriched. Calling set_user_data will increment
          times_seen!! Don't do this unless you mean to.
        - BEWARE STOMPING ON THE FLAGS WITH UPDATE if you call with the same locally cached data
          object, this is a risk you need to manage.

    HOW IT WORKS:
        - Uses Lua scripts to ensure atomicity across multiple processes or services using the same
          cache.
        - The Lua scripts are registered for each call for simplicity: this is lightning fast and
          keeps the code homed with the calls for easy viewing. Strictly suboptimal but it's not
          that bad. I promise.
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis

from server.config import Config


@dataclass
class CachedViewerSighting:
    username: str
    times_seen: int
    enriched: bool
    aggregated: bool
    timestamp: datetime


class ViewerSightingsCache:
    def __init__(self, num_shards: int = 4) -> None:
        self._num_shards: int = num_shards
        self._shards: list[redis.Redis] = [
            redis.Redis(**Config.get_redis_args()) for _ in range(num_shards)
        ]
        self.key_prefix = "viewer_sighting"

    def _get_shard(self, username: str) -> redis.Redis:
        hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
        return self._shards[hash_value % self._num_shards]

    def _get_key(self, username: str) -> str:
        return f"{self.key_prefix}:{username}"

    async def increment_times_seen(self, username: str) -> int:
        key = self._get_key(username)
        shard = self._get_shard(username)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Atomically increment times_seen for a given username
        increment_script: str = """
        local current = redis.call('HINCRBY', KEYS[1], 'times_seen', 1)
        redis.call('HSET', KEYS[1], 'timestamp', ARGV[1])
        return current
        """

        script = shard.register_script(increment_script)
        result = await script(keys=[key], args=[timestamp])
        return result

    async def set_enriched(self, username: str, enriched: bool) -> bool:
        key = self._get_key(username)
        shard = self._get_shard(username)

        script = """
        if redis.call('EXISTS', KEYS[1]) == 1 then
            redis.call('HSET', KEYS[1], 'enriched', ARGV[1])
            return 1
        else
            return 0
        end
        """

        set_enriched_script = shard.register_script(script)
        result = await set_enriched_script(keys=[key], args=[json.dumps(enriched)])
        return result == 1

    async def set_aggregated(self, username: str, aggregated: bool) -> bool:
        key = self._get_key(username)
        shard = self._get_shard(username)

        script = """
        if redis.call('EXISTS', KEYS[1]) == 1 then
            redis.call('HSET', KEYS[1], 'aggregated', ARGV[1])
            return 1
        else
            return 0
        end
        """

        set_aggregated_script = shard.register_script(script)
        result = await set_aggregated_script(keys=[key], args=[json.dumps(aggregated)])
        return result == 1

    async def get_user_data(self, username: str) -> Optional[CachedViewerSighting]:
        """Fetches cached viewer observation, or None if not present in the cache.

        Args:
            username (str): The targeted login name.

        Returns:
            Optional[CachedViewerSighting]: The stored data, or None if the login name isn't in the
            cache.
        """
        key: str = self._get_key(username)
        shard: redis.Redis = self._get_shard(username)
        fetch_script = """
        local data = redis.call('HGETALL', KEYS[1])
        if next(data) == nil then
            return nil
        end
        return data
        """
        fetch_script_sha = await shard.script_load(fetch_script)
        data = await shard.evalsha(fetch_script_sha, 1, key)

        if not data:
            return None

        data_dict = {data[i]: data[i + 1] for i in range(0, len(data), 2)}

        return CachedViewerSighting(
            username=username,
            times_seen=int(data_dict.get("times_seen", 0)),
            enriched=json.loads(data_dict.get("enriched", "false")),
            aggregated=json.loads(data_dict.get("aggregated", "false")),
            timestamp=datetime.fromisoformat(
                data_dict.get("timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )

    async def set_user_data(self, sighting: CachedViewerSighting) -> None:
        key = self._get_key(sighting.username)
        shard = self._get_shard(sighting.username)

        # Lua script to either insert new data or update existing data atomically
        upsert_script = """
        if redis.call('EXISTS', KEYS[1]) == 1 then
            redis.call('HINCRBY', KEYS[1], 'times_seen', 1)
            redis.call('HSET', KEYS[1], 'enriched', ARGV[1])
            redis.call('HSET', KEYS[1], 'aggregated', ARGV[2])
            redis.call('HSET', KEYS[1], 'timestamp', ARGV[3])
        else
            redis.call('HSET', KEYS[1], 'times_seen', ARGV[4])
            redis.call('HSET', KEYS[1], 'enriched', ARGV[1])
            redis.call('HSET', KEYS[1], 'aggregated', ARGV[2])
            redis.call('HSET', KEYS[1], 'timestamp', ARGV[3])
        end
        return nil
        """

        update_script = shard.register_script(upsert_script)
        await update_script(
            keys=[key],
            args=[
                json.dumps(sighting.enriched),
                json.dumps(sighting.aggregated),
                sighting.timestamp.isoformat(),
                sighting.times_seen,
            ],
        )

    async def _load_clear_script(self, shard: redis.Redis):
        """Use a Lua script to ensure atomicity."""
        script = """
        local cursor = "0"
        repeat
            local result = redis.call("SCAN", cursor, "MATCH", KEYS[1])
            cursor = result[1]
            local keys = result[2]
            if #keys > 0 then
                for i, key in ipairs(keys) do
                    redis.call("DEL", key)
                end
            end
        until cursor == "0"
        return true
        """
        return await shard.script_load(script)

    async def clear_cache(self) -> None:
        tasks = []
        for shard in self._shards:
            clear_script = await self._load_clear_script(shard)
            tasks.append(shard.evalsha(clear_script, 1, f"{self.key_prefix}:*"))
        await asyncio.gather(*tasks)


# Example usage
# if __name__ == "__main__":
#     cache = ViewerSightingsCache()

#     # Increment times seen and update timestamp
#     cache.increment_times_seen("example_user")

#     # Set enriched and aggregated flags
#     cache.set_enriched("example_user", True)
#     cache.set_aggregated("example_user", False)

#     # Get user data
#     user_data = cache.get_user_data("example_user")
#     print(user_data)
