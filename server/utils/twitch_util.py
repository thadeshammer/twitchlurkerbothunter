from datetime import datetime

import pytz


def convert_timestamp_from_twitch(date_str: str) -> str:
    # Parse the date string to a naive datetime object
    dt_naive = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    # Make the datetime object timezone-aware
    dt_aware = dt_naive.replace(tzinfo=pytz.UTC)
    # Format the datetime object to the desired string format
    return dt_aware.strftime("%Y-%m-%d %H:%M:%S%z")
