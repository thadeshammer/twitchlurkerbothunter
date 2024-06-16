# app/models/channel_viewerlist_fetch.py
# A channel_viewerlist_fetch represents the reception of the viewer list and associatd metadata.
# For our purposes, it is a set of ViewerSightings in a given Channel during a Scan.
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, relationship  # type: ignore

from app.db import Base


class ChannelViewerListFetch(Base):
    """SQLAlchemy model representing a Channel Viewlist Fetch event from the Viewer List Fetcher.
    The Viewer List Fetcher will negotiate and handle the reception and parsing of the viewer list
    and will create rows in the ViewerSightings table for each name. This table tracks data of
    interest for the channel(s) in question.

    ID Attributes:
        fetch_id (str): PK. UUID of this channel's Viewerlist Fetch Action.
        scanning_session_id (str): FK. UUID of the parent Scanning Session.

    Attributes from 'Get Streams' Twitch backend API endpoint:
        channel_owner_id (int): Twitch UUID of the channel this Viewerlist Fetch Action took place
            in; the broadcaster's account id.
        channel_owner_login (str): Name of the channel (broadcaster's login name) the viewerlist was
            fetched from.
        channel_owner_display_name (str): Display name of the channel, can contain non-Latin
            characters and mixed case capitalizaion.
        stream_id (int): Twitch UUID of the given stream/broadcast. Useful for tracking different
            streams for the same channel.
        category (str): The category that the channel was streaming under (e.g. 'Just Chatting').
        category_id (int): Twitch UUID for the category.
        language (str): ISO 639-1 lanuage code of the stream.
        is_mature (bool): Whether the given channel is flagged as "For mature audiences."
        was_live (bool): Whether the channel was (still) live when the viewerlist fetch took place.
        tag_ids (list): List of tag IDs that were ascribed to this stream.

        viewer_count (int): The reported viewer count for the stream at the time of the fetch.
        channel_created_at (DateTime): The timestamp of the broadcaster's account creation.

    Attributes from our data collection:
        time_of_fetch (DateTime): Timestamp of when this fetch action took place.
        time_in_channel (float): Time elapsed by the Viewer List Fetcher worker in this channel,
            clocked with time.perf_counter().

    Relationships:
        scanning_session ():
        viewer_sightings ():
    """

    __tablename__ = "channel_viewerlist_fetch"

    fetch_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    scanning_session_id = Column(
        CHAR(36), ForeignKey("scanning_session.scanning_session_id"), nullable=False
    )

    channel_owner_id = Column(BigInteger, nullable=False)  # 'user_id'
    channel_owner_login = Column(String(40), nullable=False)  # 'user_login'
    channel_owner_display_name = Column(String(40), nullable=False)  # 'user_name'
    stream_id = Column(
        BigInteger, nullable=False
    )  # 'id' UUID of this specific live-stream
    category = Column(String(40), nullable=False)  # 'game_name'
    category_id = Column(BigInteger, nullable=False)  # 'game_id'
    language: Column(
        CHAR(2), nullable=False
    )  # 'language', ISO 639-1, always two char long.
    is_mature: Column(Boolean, nullable=False)  # 'is_mature'
    was_live: Column(
        Boolean, nullable=False
    )  # the 'type' field is either "live" or "" for down.
    tag_ids: Mapped[list] = Column(JSON, default=[])

    viewer_count = Column(Integer, nullable=False)  # 'view_count'

    # not tracked: thumbnail_url, title

    stream_started_at = Column(DateTime, nullable=False)  # 'started_at'
    channel_created_at = Column(DateTime, nullable=False)  # 'created_at' in 'Get User'

    time_of_fetch = Column(DateTime, nullable=False)
    time_in_channel = Column(
        Float, nullable=False
    )  # use time.perf_counter() to measure, returns fractional seconds

    scanning_session = relationship(
        "ScanningSession", back_populates="channel_viewerlist_fetches"
    )
    viewer_sightings = relationship(
        "ViewerSighting", back_populates="channel_viewerlist_fetch"
    )
