# app/models/viewer_sighting.py
# SQLAlchemy model representing sightings of Twitch login names in a channel, and Pydantic models.
from uuid import uuid4

from pydantic import UUID4, BaseModel, Field, constr
from sqlalchemy import Boolean, Column, ForeignKey, Index, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base

from ._validator_regexes import TWITCH_LOGIN_NAME_REGEX


class ViewerSighting(Base):
    """Events-style table for tracking sightings of viewer-names across Scanning Sessions. The order
    of operations is this:

    - List of live channels is curated by the Scan Conductor.
    - Scan Conductor dispatches target channel names to the Viewer List Fetcher worker(s).
    - Viewer List Fetcher joins the target stream chat, receives viewer list, and parts from chat.
    - Viewer List Fetcher parses the viewer list, making one entry per login name in this table.

    This table is light weight and has no incoming dependencies as it's projected to potentially get
    very, very long and will likely be subject to regular pruning.

    NOTE Previously the "Observations" table.

    Attributes:
        viewer_sighting_id (str): UUID for this sighting.
        viewerlist_fetch_id (str): [FK] UUID with the associated viewerlist fetch (for a given
            stream).
        viewer_login_name (str): The login name, which is all we get from the fetch. It's unique,
            all lowercase, and used for the user's own auth and in general for Twitch back-end API
            calls. The User Data Fetcher will pull data of interest on each user for the
            TwitchUserData table, which will not have a direct relationship with this table.

        processed_by_user_data_enricher (bool): Flag showing whether this entry has been processed
            by the User Data Enricher.
        processed_by_viewer_sighting_aggregator (bool): Flag showing whether this entry has been
            processed by the Viewer Sighting Aggregator.

    Relationships:
        stream_viewerlist_fetch: Many-to-One with the ChannelViewerListFetch table.
    """

    __tablename__ = "viewer_sightings"

    viewer_sighting_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid4())
    )
    viewerlist_fetch_id = Column(
        CHAR(36), ForeignKey("stream_viewerlist_fetch.fetch_id"), nullable=False
    )
    viewer_login_name = Column(
        String(40), nullable=False
    )  # This will NOT be unique IN THIS TABLE.

    # Has this been processed by the Enricher yet?
    processed_by_user_data_enricher = Column(Boolean, nullable=False, default=False)

    # Has this been processed by the Aggregator yet?
    processed_by_user_sighting_aggregator = Column(
        Boolean, nullable=False, default=True
    )

    # Relationships
    stream_viewerlist_fetch = relationship(
        "StreamViewerListFetch", back_populates="viewer_sightings"
    )  # many viewer_sightings to one stream_viewerlist_fetch

    # indexes
    __table_args__ = (Index("ix_viewer_login_name", "viewer_login_name"),)


class ViewerSightingBase(BaseModel):
    """
    Base model for Viewer Sighting with viewer_login_name validator.

    NOTE. This login name comes from the 353 message (which is a space-seperated list) and not
    a Helix response, hence the naming difference from the other Pydantic machines.
    """

    viewer_login_name: constr(regex=TWITCH_LOGIN_NAME_REGEX) = Field(...)


class ViewerSightingCreate(ViewerSightingBase):
    """Model for creating a new Viewer Sighting entry to persist in the db."""


class ViewerSightingRead(ViewerSightingBase):
    """Model for returning Viewer Sighting data from the db."""

    viewer_sighting_id: UUID4 = Field(...)
    viewerlist_fetch_id: UUID4 = Field(...)

    class Config:
        orm_mode = True
