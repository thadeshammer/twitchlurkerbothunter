# server/models/viewer_sighting.py
# SQLModel representing sightings of Twitch login names in a given channel.
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import StringConstraints
from sqlmodel import Field, SQLModel

from .._validator_regexes import TWITCH_LOGIN_NAME_REGEX


class ViewerSightingBase(SQLModel, table=False):
    viewer_login_name: Annotated[
        str,
        StringConstraints(pattern=TWITCH_LOGIN_NAME_REGEX),
        Field(..., index=True),
    ]
    processed_by_user_data_enricher: bool = Field(default=False, nullable=False)
    processed_by_user_sighting_aggregator: bool = Field(default=False, nullable=False)


class ViewerSighting(ViewerSightingBase, table=True):
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
        id (str): UUID for this sighting.
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

    __tablename__: str = "viewer_sightings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    viewerlist_fetch_id: UUID = Field(
        foreign_key="stream_viewerlist_fetch.fetch_id", nullable=False
    )


class ViewerSightingCreate(ViewerSightingBase):
    """Model for creating a new Viewer Sighting entry to persist in the db."""


class ViewerSightingRead(ViewerSightingBase):
    """Model for returning Viewer Sighting data from the db."""

    ID: UUID
