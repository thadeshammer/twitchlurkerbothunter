import asyncio
from multiprocessing import Process, Queue

import pytest

from app.util.shard_cache import ShardCache


def worker(cache: ShardCache, task_queue: Queue, result_queue: Queue):
    async def async_worker():
        while True:
            task = task_queue.get()
            if task is None:
                break

            key, value = task
            await cache.set(key, value)
            result = await cache.get(key)
            result_queue.put((key, result))

    asyncio.run(async_worker())


@pytest.mark.asyncio
async def test_multiprocessing_and_locking():
    num_shards = 4
    cache = ShardCache(num_shards)

    task_queue = Queue()
    result_queue = Queue()

    # Create and start worker processes
    processes = [
        Process(target=worker, args=(cache, task_queue, result_queue)) for _ in range(4)
    ]
    for p in processes:
        p.start()

    # Enqueue tasks
    for i in range(100):
        task_queue.put((f"key{i}", f"value{i}"))

    # Signal workers to exit
    for _ in processes:
        task_queue.put(None)

    # Collect results
    results = {}
    while len(results) < 100:
        key, value = result_queue.get()
        results[key] = value

    # Ensure all processes have finished
    for p in processes:
        p.join()

    # Validate results
    for i in range(100):
        assert results[f"key{i}"] == f"value{i}"
