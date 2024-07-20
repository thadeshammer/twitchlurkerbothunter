# tests/utils/shared_queue
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
from unittest.mock import patch

import pytest
import pytest_asyncio
from redis.exceptions import RedisError

from server.config import Config
from server.utils import RedisSharedQueue, RedisSharedQueueError, RedisSharedQueueFull


@pytest_asyncio.fixture(scope="function")
async def shared_queue(redis_client):
    queue = RedisSharedQueue(name="testqueue", **Config.get_redis_args())
    await queue.clear()
    yield queue
    await queue.clear()


@pytest.mark.asyncio
async def test_enqueue_and_dequeue(shared_queue):
    await shared_queue.enqueue("item1")
    await shared_queue.enqueue("item2")

    size = await shared_queue.queue_size()
    assert size == 2

    item = await shared_queue.dequeue()
    assert item[0] == "item1"
    assert item[1] == {}

    item = await shared_queue.dequeue()
    assert item[0] == "item2"
    assert item[1] == {}

    size = await shared_queue.queue_size()
    assert size == 0


@pytest.mark.asyncio
async def test_queue_size(shared_queue):
    initial_size = await shared_queue.queue_size()
    assert initial_size == 0

    await shared_queue.enqueue("item1")

    size = await shared_queue.queue_size()
    assert size == 1


@pytest.mark.asyncio
async def test_empty(shared_queue):
    assert await shared_queue.empty()

    await shared_queue.enqueue("item1")
    assert not await shared_queue.empty()


@pytest.mark.asyncio
async def test_clear(shared_queue):
    await shared_queue.enqueue("item1")
    await shared_queue.enqueue("item2")

    await shared_queue.clear()

    size = await shared_queue.queue_size()
    assert size == 0


@pytest.mark.asyncio
async def test_size_limit():
    queue = RedisSharedQueue(
        name="limitedqueue", size_limit=1, **Config.get_redis_args()
    )

    await queue.clear()

    assert (await queue.remaining_space()) == 1

    await queue.enqueue("item1")

    assert (await queue.remaining_space()) == 0

    with pytest.raises(RedisSharedQueueFull):
        await queue.enqueue("item2")

    await queue.clear()


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_enqueue_failure(shared_queue):
    with patch.object(shared_queue, "_enqueue", side_effect=RedisError("rpush failed")):
        with pytest.raises(RedisSharedQueueError, match="Failed to enqueue."):
            await shared_queue.enqueue("item")


@pytest.mark.asyncio
@patch("redis.asyncio.Redis.blpop", side_effect=RedisError("blpop failed"))
async def test_dequeue_failure(mock_blpop, shared_queue):
    failure_result = await shared_queue.dequeue()
    assert failure_result == (None, {})


@pytest.mark.asyncio
@patch("redis.asyncio.Redis.delete", side_effect=RedisError("delete failed"))
async def test_clear_failure(mock_delete, shared_queue):
    with pytest.raises(RedisSharedQueueError, match="Failed to clear queue."):
        await shared_queue.clear()
