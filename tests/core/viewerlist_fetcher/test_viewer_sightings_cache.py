# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import asyncio
from datetime import datetime, timezone

import pytest
import pytest_asyncio

from server.core.viewerlist_fetcher.viewer_sightings_cache import (
    CachedViewerSighting,
    ViewerSightingsCache,
)


@pytest_asyncio.fixture(scope="function")
async def viewer_sightings_cache(redis_client):
    cache = ViewerSightingsCache()
    tasks = []
    for i in range(cache._num_shards):
        tasks.append(cache._shards[i].flushdb())
    await asyncio.gather(*tasks)

    yield cache

    tasks = []
    for i in range(cache._num_shards):
        tasks.append(cache._shards[i].flushdb())
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_increment_times_seen(viewer_sightings_cache: ViewerSightingsCache):
    username = "test_user"
    await viewer_sightings_cache.set_user_data(
        CachedViewerSighting(
            username=username,
            times_seen=3,
            enriched=False,
            aggregated=False,
            timestamp=datetime.now(timezone.utc),
        )
    )

    result = await viewer_sightings_cache.increment_times_seen(username)
    sighting = await viewer_sightings_cache.get_user_data(username)
    assert result == 4
    assert sighting.times_seen == 4
    assert sighting.username == username


@pytest.mark.asyncio
async def test_set_enriched(viewer_sightings_cache):
    username = "test_user"
    await viewer_sightings_cache.set_user_data(
        CachedViewerSighting(
            username=username,
            times_seen=3,
            enriched=False,
            aggregated=False,
            timestamp=datetime.now(timezone.utc),
        )
    )

    await viewer_sightings_cache.set_enriched(username, True)
    sighting = await viewer_sightings_cache.get_user_data(username)
    assert sighting.enriched is True
    assert sighting.username == username


@pytest.mark.asyncio
async def test_set_aggregated(viewer_sightings_cache):
    username = "test_user"
    await viewer_sightings_cache.set_user_data(
        CachedViewerSighting(
            username=username,
            times_seen=3,
            enriched=False,
            aggregated=False,
            timestamp=datetime.now(timezone.utc),
        )
    )

    await viewer_sightings_cache.set_aggregated(username, True)
    sighting = await viewer_sightings_cache.get_user_data(username)
    assert sighting.aggregated is True
    assert sighting.username == username


@pytest.mark.asyncio
async def test_get_user_data(viewer_sightings_cache):
    username = "test_user"
    times_seen = 5
    enriched = True
    aggregated = False
    timestamp = datetime.now(timezone.utc)

    sighting = CachedViewerSighting(
        username=username,
        times_seen=times_seen,
        enriched=enriched,
        aggregated=aggregated,
        timestamp=timestamp,
    )
    await viewer_sightings_cache.set_user_data(sighting)
    retrieved_sighting = await viewer_sightings_cache.get_user_data(username)

    assert retrieved_sighting.username == username
    assert retrieved_sighting.times_seen == times_seen
    assert retrieved_sighting.enriched == enriched
    assert retrieved_sighting.aggregated == aggregated
    assert retrieved_sighting.timestamp == timestamp


@pytest.mark.asyncio
async def test_set_user_data(viewer_sightings_cache):
    username = "test_user"
    times_seen = 3
    enriched = False
    aggregated = True
    timestamp = datetime.now(timezone.utc)

    sighting = CachedViewerSighting(
        username=username,
        times_seen=times_seen,
        enriched=enriched,
        aggregated=aggregated,
        timestamp=timestamp,
    )
    await viewer_sightings_cache.set_user_data(sighting)
    retrieved_sighting = await viewer_sightings_cache.get_user_data(username)

    assert retrieved_sighting.username == username
    assert retrieved_sighting.times_seen == times_seen
    assert retrieved_sighting.enriched == enriched
    assert retrieved_sighting.aggregated == aggregated
    assert retrieved_sighting.timestamp == timestamp
