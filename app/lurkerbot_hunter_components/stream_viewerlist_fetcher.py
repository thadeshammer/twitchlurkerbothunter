# TODO the path to this file and this file's name.
"""
    StreamViewerListFetcher

    The single responsibilty of this component is to fetch a viewerlist from a target stream.

    Procedure:
        - Select TARGET_STREAM from workbench. (If none, wait.)
        - Create a new StreamViewerListFetch for TARGET_STREAM with stream data.
        - Join the IRC chat for TARGET_STREAM.
        - Receive the 353 message.
        - Part from the IRC chat.
        - Create ViewerSightings for each login name in the 353 message.
        - Go back to step 1 and repeat.

    Will use the multiprocesses library (Py built-in) to support multiple concurrent workers.
    Each worker will have its own "workbench"
    
    RATE LIMITING
    
    Configurable hard limits on quantity of chat-joins per window. Docs say it's 20 joins per 10s.
    We could play very safely and cap at 18 joins per 10s OR 20 joins per 10.2s, etc.

    NOTE. The list of viewers in the 353 is reported to be capped at around 100, and it seems like
    it will always include the streamer themself, as well as moderators and VIPS.
"""
