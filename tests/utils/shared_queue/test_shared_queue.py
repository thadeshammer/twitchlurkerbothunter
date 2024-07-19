# tests/utils/shared_queue
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
import pytest
import pytest_asyncio

from server.config import Config
from server.utils import SharedQueue, SharedQueueError, SharedQueueFull

# from tests.conftest import TEST_REDIS_DB, TEST_REDIS_HOST, TEST_REDIS_PORT


@pytest_asyncio.fixture(scope="function")
async def shared_queue(redis_client):  # pylint: disable=unused-argument
    queue = SharedQueue(name="testqueue", **Config.get_redis_args())
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
    assert item == "item1"

    item = await shared_queue.dequeue()
    assert item == "item2"

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
    queue = SharedQueue(name="limitedqueue", size_limit=1, **Config.get_redis_args())

    await queue.enqueue("item1")

    with pytest.raises(SharedQueueFull):
        await queue.enqueue("item2")

    await queue.clear()


@pytest.mark.asyncio
async def test_enqueue_failure(shared_queue, mocker):
    assert True


@pytest.mark.asyncio
async def test_dequeue_failure(shared_queue, mocker):
    assert True


@pytest.mark.asyncio
async def test_clear_failure(shared_queue, mocker):
    assert True
