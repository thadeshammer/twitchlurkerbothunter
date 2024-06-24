"""
    UserDataEnricher

    This component will process entries in ViewerSightings in batches.

    For each ViewerSighting:
    - If a viewer is unknown (hasn't yet been seen by the bot) it gets an entry in TwitchUserData.
    - If a viewer is known, and it's last sighting is not the current scan, its TwitchUserData is
    updated.
    - If a viewer is known and it's last sighting was this current scan, it's ignored.

    Creating or Updating a TwitchUserData entry will require a call to the Twitch Helix API 'Get
    Users' endpoint, which can be done in batches of 100, so we'll want to buffer them up.

    With the bearer token, the rate limit is 120 requests per minute, or we get a 429. The response
    headers are supposed to include the following headers with each response to help one stay within
    the request limits.

    'Ratelimit-Limit' — The rate at which points are added to your bucket.
    'Ratelimit-Remaining' — The number of points in your bucket.
    'Ratelimit-Reset' — A Unix epoch timestamp that identifies when your bucket is reset to full.

"""
