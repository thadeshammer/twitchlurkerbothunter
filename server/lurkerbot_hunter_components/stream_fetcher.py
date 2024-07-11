# TODO path and filename
"""
    StreamFetcher

    The single responsiblity of this manage the list of live streams that are a part of the current
    scan.
    
    Per configuration (defaults) OR parameters from the API request, it will call the 'Get Streams'
    endpoint, further filter the results, and populate a queue for the ScanConductor.

    This also will be run in multiprocess and with asyncio so it's not blocking and the
    StreamViewerListFetcher can work in parallel.
"""
