import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

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
            redis.Redis(**Config.get_redis_args(), decode_responses=True)
            for _ in range(num_shards)
        ]
        self._increment_script: str = """
        local current = redis.call('HINCRBY', KEYS[1], 'times_seen', 1)
        redis.call('HSET', KEYS[1], 'timestamp', ARGV[1])
        return current
        """

    def _get_shard(self, username: str) -> redis.Redis:
        hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
        return self._shards[hash_value % self._num_shards]

    def _get_key(self, username: str) -> str:
        return f"viewer:{username}"

    async def increment_times_seen(self, username: str) -> int:
        key = self._get_key(username)
        shard = self._get_shard(username)
        timestamp = datetime.now(timezone.utc).isoformat()
        script = shard.register_script(self._increment_script)
        result = await script(keys=[key], args=[timestamp])
        return result

    async def set_enriched(self, username: str, enriched: bool) -> None:
        key = self._get_key(username)
        shard = self._get_shard(username)
        await shard.hset(key, "enriched", json.dumps(enriched))

    async def set_aggregated(self, username: str, aggregated: bool) -> None:
        key = self._get_key(username)
        shard = self._get_shard(username)
        await shard.hset(key, "aggregated", json.dumps(aggregated))

    async def get_user_data(self, username: str) -> CachedViewerSighting:
        key: str = self._get_key(username)
        shard: redis.Redis = self._get_shard(username)
        data = await shard.hgetall(key)
        return CachedViewerSighting(
            username=username,
            times_seen=int(data.get("times_seen", 0)),
            enriched=json.loads(data.get("enriched", "false")),
            aggregated=json.loads(data.get("aggregated", "false")),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )

    async def set_user_data(self, sighting: CachedViewerSighting) -> None:
        key = self._get_key(sighting.username)
        shard = self._get_shard(sighting.username)
        await shard.hset(
            key,
            mapping={
                "times_seen": sighting.times_seen,
                "enriched": json.dumps(sighting.enriched),
                "aggregated": json.dumps(sighting.aggregated),
                "timestamp": sighting.timestamp.isoformat(),
            },
        )


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
