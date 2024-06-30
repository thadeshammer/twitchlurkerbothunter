# app/models/stream_viewerlist_fetch.py
# SQLAlchemy model representing a single viewerlist fetch event of a target stream.

"""StreamViewerListFetch model and validators.

    Each row represents a single viewer-list fetch event of a target stream: the reception of the
    viewer list and associated metadata. (For our purposes, it is a set of ViewerSightings in a
    given channel during a scan.)

    The Pydantic BaseModels are split into two representing the relevant Twitch API Response data
    and the in-app metadata, and they're brought together by the
    merge_stream_viewerlist_fetch_data() function.

SQLAlchemy Model:
    StreamViewerListFetch: The SQLAlchemy model

Pydantic Models:
    StreamViewerListFetchTwitchAPIResponse: Pydantic model to validate Twitch API response data.
    StreamViewerListFetchAppData: Pydantic model to validate app-generated data.
    StreamViewerListFetchCreate: For making a new DB row.
    StreamViewerListFetchRead For retrieving and working with an existing DB row.

Merging Function:
    merge_stream_viewerlist_fetch_data
"""
from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import UUID4, BaseModel, Field, confloat, conint, constr, validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class StreamViewerListFetchStatus(StrEnum):
    # it's on the list to be scanned (and it has an entry in the StreamViewerListFetch table)
    PENDING = "pending"
    # given to a worker, i.e. it's on a "workbench" (it's in the "respect the rate limit" buffer)
    IN_QUEUE = "in_queue"
    # it's being worked on by the worker, "processing"
    WAITING_ON_VIEWER_LIST = "waiting_on_viewer_list"
    # the list has been fetched
    COMPLETE = "complete"


class StreamViewerListFetch(Base):
    """SQLAlchemy model representing a Stream Viewlist Fetch event from the Viewer List Fetcher.
    The Viewer List Fetcher will negotiate and handle the reception and parsing of the viewer list
    and will create rows in the ViewerSightings table for each name. This table tracks data of
    interest for the streams/channel(s) in question.

    ID Attributes:
        fetch_id (str): PK. UUID of this channel's Viewerlist Fetch Action.
        scanning_session_id (str): [FK] UUID of the parent Scanning Session.

    Attributes from our data collection:
        fetch_action_at (DateTime): Timestamp of when this fetch action took place.
        duration_of_fetch_action (float): Time elapsed by the Viewer List Fetcher worker in this
            stream's chat, clocked with time.perf_counter().
        fetch_status (StreamViewerListFetchStatus): the last recorded state of this fetch action.

    Attributes from 'Get Streams' Twitch backend API endpoint:
        stream_id (int): Twitch UUID of the given stream/broadcast. Useful for tracking different
            streams for the same channel.
        channel_owner_id (int): [FK] Twitch UUID of the channel this Viewerlist Fetch Action took
            place in; the broadcaster's account id.
        category_id (int): Twitch UUID for the category.
        was_live (bool): Whether the channel was (still) live when the viewerlist fetch took place.
        viewer_count (int): The reported viewer count for the stream at the time of the fetch.
        stream_started_at (DateTime): The go-live timestamp of this live stream.
        language (str): ISO 639-1 lanuage code of the stream.
        is_mature (bool): Whether the given channel is flagged as "For mature audiences."

    Relationships:
        scanning_session (): many stream_viewerlist_fetches to one scanning_session
        twitch_user_data (): # one-to-one (this relationship mapping is for the user of THIS STREAM)
        viewer_sightings (): many viewer_sightings to one stream_viewerlist_fetch
    """

    __tablename__ = "stream_viewerlist_fetch"

    fetch_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    fetch_action_at = Column(DateTime, nullable=False)
    duration_of_fetch_action = Column(
        Float, nullable=False
    )  # use time.perf_counter() to measure, returns fractional seconds
    fetch_status = Column(
        String(25), nullable=False, default=StreamViewerListFetchStatus.PENDING
    )

    # foreign keys
    scanning_session_id = Column(
        CHAR(36),
        ForeignKey("scanning_sessions.scanning_session_id"),
        nullable=False,
        index=True,
    )
    channel_owner_id = Column(
        BigInteger,
        ForeignKey("twitch_user_data.twitch_account_id"),
        nullable=False,
        index=True,
    )  # 'user_id'
    category_id = Column(
        BigInteger,
        ForeignKey("stream_categories.category_id"),
        nullable=False,
        index=True,
    )  # 'game_id', if it's -1 it means they didn't set a category.
    # category_name should be stored in the StreamCategories table if it's new to us.

    # 'Get Stream' response data
    viewer_count = Column(Integer, nullable=False)  # 'viewer_count' for this broadcast
    stream_id = Column(
        BigInteger, unique=True, nullable=False
    )  # 'id' UUID of this specific live-stream
    stream_started_at = Column(DateTime, nullable=False)  # 'started_at'
    language = Column(
        CHAR(2), nullable=False
    )  # 'language', ISO 639-1, always two char long.
    is_mature = Column(Boolean, nullable=False)  # 'is_mature'
    was_live = Column(
        Boolean, nullable=False
    )  # the 'type' field is either "live" or "" for down.

    # not tracked: thumbnail_url, title,

    # relationships
    scanning_session = relationship(
        "ScanningSession", back_populates="stream_viewerlist_fetches"
    )  # many stream_viewerlist_fetches to one scanning_session
    twitch_user_data = relationship(
        "TwitchUserData", back_populates="stream_viewerlist_fetch"
    )  # one-to-one (this relationship mapping is for the user of THIS STREAM)
    viewer_sightings = relationship(
        "ViewerSighting", back_populates="stream_viewerlist_fetch"
    )  # many viewer_sightings to one stream_viewerlist_fetch
    stream_category = relationship(
        "StreamCategory", back_populates="stream_viewerlist_fetch"
    )
