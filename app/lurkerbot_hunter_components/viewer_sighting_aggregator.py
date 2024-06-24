# TODO path and name
"""
    ViewerSightingAggregator

    This component will iterate over all ViewerSightings for the current ScanningSession and tally
    up how many streams each viewer was spotted in during the scan.

    HOW TO DO THIS?

    It could process it in batches and update TwitchUserData.most_recent_concurrent_channel_count
    each  batch, treating it as an accumulator. This would mean we'd still get some data for partial
    scans.

    It could tally and cache the results in memory then commit them all as a single transaction.
    This is more volatile; does it gain us anything?
"""
