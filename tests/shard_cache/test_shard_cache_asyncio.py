import asyncio

import pytest

from app.util.shard_cache import ShardCache


@pytest.mark.asyncio
async def test_set_and_get():
    cache = ShardCache(num_shards=4)

    await cache.set("key1", "value1")
    value = await cache.get("key1")
    assert value == "value1"

    await cache.set("key2", "value2")
    value = await cache.get("key2")
    assert value == "value2"


@pytest.mark.asyncio
async def test_update():
    cache = ShardCache(num_shards=4)

    await cache.set("key1", "initial_value")
    value = await cache.get("key1")
    assert value == "initial_value"

    await cache.set("key1", "updated_value")
    value = await cache.get("key1")
    assert value == "updated_value"


@pytest.mark.asyncio
async def test_delete():
    cache = ShardCache(num_shards=4)

    await cache.set("key1", "value1")
    value = await cache.get("key1")
    assert value == "value1"

    await cache.delete("key1")
    value = await cache.get("key1")
    assert value is None


@pytest.mark.asyncio
async def test_concurrent_access():
    cache = ShardCache(num_shards=4)

    async def worker(key, value):
        await cache.set(key, value)
        return await cache.get(key)

    tasks = [asyncio.create_task(worker(f"key{i}", f"value{i}")) for i in range(100)]
    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        assert result == f"value{i}"
