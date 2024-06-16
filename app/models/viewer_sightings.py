# app/models/viewer_sighting.py
# SQLAlchemy model representing sightings of Twitch login names in a channel.
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class ViewerSighting(Base):
    """Events-style table tracking sightings of viewer-names across Scanning Sessions. The order of
    operations is this:

    - List of live channels is curated by the Scan Conductor.
    - Scan Conductor dispatches target channel names to the Viewer List Fetcher worker(s).
    - Viewer List Fetcher joins the target channel, receives viewer list, and parts from channel.
    - Viewer List Fetcher parses the viewer list, making one entry per login name in this table.

    This table is light weight and has no incoming dependencies as it's projected to potentially get
    very, very long and will likely be subject to regular pruning.

    NOTE Previously the "Observations" table.

    Attributes:
        viewer_sighting_id (str): UUID for this sighting.
        viewerlist_fetch_id (str): FK UUID with the associated viewerlist fetch (for a given
            channel).
        viewer_login_name (str): The login name, which is all we get from the fetch. It's unique,
            all lowercase, and used for the user's own auth and in general for Twitch back-end API
            calls. The User Data Fetcher will pull data of interest on each user for the
            TwitchUserData table, which will not have a direct relationship with this table.

    Relationships:
        channel_viewerlist_fetch: Many-to-One with the ChannelViewerListFetch table.
    """

    __tablename__ = "viewer_sightings"

    viewer_sighting_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid4())
    )
    viewerlist_fetch_id = Column(
        CHAR(36), ForeignKey("stream_viewerlist_fetch.fetch_id"), nullable=False
    )
    viewer_login_name = Column(String(40), nullable=False)

    # Relationships
    stream_viewerlist_fetch = relationship(
        "StreamViewerListFetch", back_populates="viewer_sightings"
    )  # many viewer_sightings to one stream_viewerlist_fetch
