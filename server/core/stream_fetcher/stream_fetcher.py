# TODO path and filename
"""
    StreamFetcher

    The single responsiblity of this module is to fetch the list of live streams that are a part of
    the current scan.
    
    Per configuration (defaults) OR parameters from the API request, it will call the 'Get Streams'
    endpoint, further filter the results, and populate a queue for the ScanConductor.

    There will be ONE StreamFetcher process per scanning_session and thus only ONE process feeding
    ONE PendingQueue (in Redis).

    Procedure:
        - Kick off the 'Get Streams' API request (turn on the fire hose) then continue paginating
          through the request.
        1. Get the next page.
        2. Process the page putting each stream info dict into Redis.
        3. Repeat until done or cancelled.
"""
