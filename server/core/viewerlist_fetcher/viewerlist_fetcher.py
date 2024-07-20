# server/core/viewerlist_fetcher/viewerlist_fetcher.py
"""
    ViewerListFetcher a.k.a. "the worker" or "line cook"

    The single responsibilty of this component is to fetch a viewerlist from a target stream within
    the rate limit. 

    Usage:
        - Spin this off in a Python multiprocess process with access to a Workbench Queue that is
          filled up to (and helps guard against breaking) the rate limit.
    Set-up:
        - Instantiate a single (ONLY ONE) ViewerlistFetcherChannelListener per ViewerListFetcher.
    Procedure:
        - Select TARGET_STREAM with TARGET_STREAM_DATA from Workbench queue. (If none, wait.)
            - This will be the 'Get Stream' dict.
            - https://dev.twitch.tv/docs/api/reference/#get-streams
        - Create a new partial TwitchUserData row for the streamer OR update existing.
        - Create a new StreamCategory row if necessary.
        - Create a new StreamViewerListFetch for TARGET_STREAM with TARGET_STREAM_DATA.
        - Kick off the ViewerlistFetcherChannelListener for TARGET_STREAM and await response.
        - Create ViewerSightings for each login name in that response.
        - Repeat.
    
    RATE LIMITING
    
    Configurable hard limits on quantity of chat-joins per window. Docs say it's 20 joins per 10s.
    We could play very safely and cap at 18 joins per 10s OR 20 joins per 10.2s, etc.
"""
