# /app.models/__init__.py
"""
Models Package for Thades' TwitchLurkerbotHunter.

This package provides the SQLAlchemy (MySQL) data models and Pydantic validation for the Lurkerbot
Hunter's data model.

Submodules:
- _validator_regexes: Helper file with regexes used for data validation in multiple places.
- scanning_session: Represents a series of viewer-list fetches from a set of live streams.
- secrets: A single row table to hold a single access and refresh token pair and associated
metadata.
- stream_categories: A table mapping Twitch stream category ID ('game_id') to name ('game_name').
- stream_viewerlist_fetch: Represents a viewer-list fetch event for a given live stream, as well as
data about the live stream and the streamer.
- suspected_bot: An extension on the Twitch User Data table with additional metadata and metrics
collected for accounts that have been classfied as lurker bots.
- twitch_user_data: Every login name observed by this app will have an entry here with 'Get User'
data.
- viewer_sightings: An events-style table where login names that are observed in viewer-lists pulled
during a scan are recorded; login names appearing more than once in a given scan will appear more
than once on this table with the same scanning_session_id, which is a big part of classifying a
lurker bot.

Author:
    Thades (thadeshammer@gmail.com)
Version:
    1.0.0
"""
from .scanning_session import (
    ScanningSession,
    ScanningSessionCreate,
    ScanningSessionRead,
    ScanningSessionStopReasonEnum,
)
from .secrets import Secret, SecretCreate, SecretRead
from .stream_categories import StreamCategory, StreamCategoryCreate, StreamCategoryRead
from .stream_viewerlist_fetch import (
    StreamViewerListFetch,
    StreamViewerListFetchCreate,
    StreamViewerListFetchRead,
    StreamViewerListFetchStatus,
)

# from .suspected_bot import (
#     SUSPICION_RANKING_THRESHOLDS,
#     SuspectedBot,
#     SuspectedBotCreate,
#     SuspectedBotRead,
#     SuspicionLevel,
#     SuspicionReason,
# )
# from .twitch_user_data import TwitchUserData, TwitchUserDataCreate, TwitchUserDataRead
from .viewer_sighting import ViewerSighting, ViewerSightingCreate, ViewerSightingRead

__all__ = [
    "ScanningSession",
    "ScanningSessionCreate",
    "ScanningSessionRead",
    "ScanningSessionStopReasonEnum",
    "Secret",
    "SecretCreate",
    "SecretRead",
    "StreamCategory",
    "StreamCategoryCreate",
    "StreamCategoryRead",
    "StreamViewerListFetch",
    "StreamViewerListFetchCreate",
    "StreamViewerListFetchRead",
    "StreamViewerListFetchStatus",
    # "SuspectedBot",
    # "SuspectedBotCreate",
    # "SuspectedBotRead",
    # "SUSPICION_RANKING_THRESHOLDS",
    # "SuspicionLevel",
    # "SuspicionReason",
    # "TwitchUserData",
    # "TwitchUserDataCreate",
    # "TwitchUserDataRead",
    "ViewerSighting",
    "ViewerSightingCreate",
    "ViewerSightingRead",
]
