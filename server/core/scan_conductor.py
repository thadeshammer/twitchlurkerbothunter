# TODO file path and name
"""
    ScanConductor

    Reponsible for:

    - Creates a new ScanningSession table entry.
    - Oversee transfer of streams-to-scan from the StreamFetcher over to the StreamViewerList
      workbench.
    - Ensure the Rate Limit is respected.
    - Updates the ScanningSession with relevant metrics both during runtime and when complete.
    
"""
