# pylint: disable=redefined-outer-name
# pylint: disable=protected-access

import asyncio
from time import perf_counter
from unittest.mock import patch

import pytest
import pytest_asyncio

from server.config import Config
from server.core.viewerlist_fetcher import Workbench
from server.utils import RedisSharedQueue

TEST_WORKBENCH_SIZE_LIMIT = 4


@pytest_asyncio.fixture(scope="function")
async def workbench():
    workbench = Workbench()
    workbench._pending_queue = RedisSharedQueue(
        name="test_pendingqueue", **Config.get_redis_args()
    )
    workbench._workbench_queue = RedisSharedQueue(
        name="test_workbenchqueue",
        size_limit=TEST_WORKBENCH_SIZE_LIMIT,
        **Config.get_redis_args(),
    )
    workbench._stopwatch = perf_counter() - 10.1
    yield workbench


@pytest.mark.asyncio
@patch("server.utils.redis_shared_queue.RedisSharedQueue.enqueue")
@patch("server.utils.redis_shared_queue.RedisSharedQueue.dequeue")
async def test_update_empty_pending_queue(mock_dequeue, mock_enqueue, workbench):
    await workbench._pending_queue.clear()
    await workbench._workbench_queue.clear()

    await workbench.update()

    mock_dequeue.assert_not_called()
    mock_enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_update_with_pending_items(workbench: Workbench):
    # workbench._stopwatch = perf_counter() - 10.1
    await workbench._pending_queue.clear()
    await workbench._workbench_queue.clear()

    # Add items to the pending queue
    await workbench._pending_queue.enqueue("item1")
    await workbench._pending_queue.enqueue("item2")
    await workbench._pending_queue.enqueue("item3")

    # Call the update method
    await workbench.update()

    # Check that dequeue and enqueue were called
    assert await workbench._pending_queue.queue_size() < 3
    assert await workbench._workbench_queue.queue_size() > 0


@pytest.mark.asyncio
async def test_update_partial_pending_queue(workbench):
    await workbench._pending_queue.clear()
    await workbench._workbench_queue.clear()

    # Add fewer items than the workbench can hold to the pending queue
    await asyncio.gather(
        workbench._pending_queue.enqueue("item1"),
        workbench._pending_queue.enqueue("item2"),
        workbench._pending_queue.enqueue("item3"),
        workbench._pending_queue.enqueue("item4"),
        workbench._pending_queue.enqueue("item5"),
    )

    await workbench.update()

    assert await workbench._workbench_queue.queue_size() == 4
    assert await workbench._pending_queue.queue_size() == 1


@pytest.mark.asyncio
async def test_update_full_workbench_queue(workbench):
    # Ensure the queues are clear
    await workbench._pending_queue.clear()
    await workbench._workbench_queue.clear()

    # Fill the workbench queue to its capacity
    for i in range(TEST_WORKBENCH_SIZE_LIMIT):
        await workbench._workbench_queue.enqueue(f"workbench_item_{i}")

    # Add items to the pending queue
    await workbench._pending_queue.enqueue("pending_item1")
    await workbench._pending_queue.enqueue("pending_item2")

    # Call the update method
    await workbench.update()

    # Check that dequeue and enqueue were not called because the workbench queue is full
    assert await workbench._pending_queue.queue_size() == 2
    assert await workbench._workbench_queue.queue_size() == TEST_WORKBENCH_SIZE_LIMIT
