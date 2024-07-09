# app/models/stream_viewerlist_fetch.py
# SQLmodel representing a single viewerlist fetch event of a target stream.

"""StreamViewerListFetch model and validators.

    Each row represents a single viewer-list fetch event of a target stream: the reception of the
    viewer list and associated metadata. (For our purposes, it is a set of ViewerSightings in a
    given channel during a scan.)

Usage:
    Create a StreamViewerListFetch with its required data, update its status as is appropriate, and
    update its duration when status is set to StreamViewerListFetchStatus.COMPLETE.

    Instantiate a StreamViewerListFetch model using the constructor: pack the relevant API response
    closure from 'Get Streams' (a single closure, not the entire list) into a dict, and pass the
    required app meta data as well. For example, here's the api_response and the Create call:

    https://dev.twitch.tv/docs/api/reference/#get-streams

    api_response_data == {
        "id": "123456789",
        "user_id": "98765",
        "user_login": "sandysanderman",
        "user_name": "SandySanderman",
        "game_id": "494131",
        "game_name": "Little Nightmares",
        "type": "live",
        "title": "hablamos y le damos a Little Nightmares 1",
        "tags": ["Español"],
        "viewer_count": 78365,
        "started_at": "2021-03-10T15:04:21Z",
        "language": "es",
        "thumbnail_url": "https://blah-blah-blah.jpg",
        "tag_ids": [],
        "is_mature": false
    }

    viewer_list_fetch = StreamViewerListFetchCreate(
        fetch_action_at,  # datetime
        duration_of_fetch_action,  # float
        fetch_status,  # StreamViewerListFetchStatus
        scanning_session_id,  # UUID
        **api_response_data  # dict[str, str]
    )

SQLModel constructs:
    StreamViewerListFetchBase: SQLModel base class with shared properties
    StreamViewerListFetch: SQLModel table model
    StreamViewerListFetchCreate: For making a new DB row.
    StreamViewerListFetchRead For retrieving and working with an existing DB row.

"""
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Optional, cast
from uuid import UUID, uuid4

from pydantic import StringConstraints, model_validator
from sqlmodel import Column
from sqlmodel import Enum as sqlmodel_Enum
from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig

from ._validator_regexes import LANGUAGE_CODE_REGEX


class StreamViewerListFetchStatus(StrEnum):
    # it's on the list to be scanned (and it has an entry in the StreamViewerListFetch table)
    PENDING = "pending"
    # given to a worker, i.e. it's on a "workbench" (it's in the "respect the rate limit" buffer)
    IN_QUEUE = "in_queue"
    # it's being worked on by the worker, "processing"
    WAITING_ON_VIEWER_LIST = "waiting_on_viewer_list"
    # the list has been fetched
    COMPLETE = "complete"


class StreamViewerListFetchBase(SQLModel):
    """SQLmodel representing a Stream Viewlist Fetch event from the Viewer List Fetcher.

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

    fetch_action_at: datetime = Field(nullable=False)
    duration_of_fetch_action: Annotated[Optional[float], Field(nullable=False, ge=0.0)]
    fetch_status: Annotated[
        StreamViewerListFetchStatus,
        Field(
            sa_column=Column(
                sqlmodel_Enum(StreamViewerListFetchStatus),
                nullable=False,
                default=StreamViewerListFetchStatus.PENDING,
            )
        ),
    ]

    channel_owner_id: Annotated[int, Field(index=True, ge=0)]
    category_id: Annotated[int, Field(index=True, ge=0)]
    viewer_count: Annotated[int, Field(..., ge=0)]
    stream_id: Annotated[int, Field(..., ge=0)]
    stream_started_at: datetime = Field(...)
    language: Annotated[str, StringConstraints(pattern=LANGUAGE_CODE_REGEX)]
    is_mature: bool = Field(...)
    was_live: bool = Field(...)

    @model_validator(mode="before")
    def transform_type_to_was_life(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Need to convert the 'type' key into the `was_live` bool."""
        if "type" in data.keys():
            data["was_live"] = data.pop("type") == "live"

        return data

    model_config = cast(
        SQLModelConfig,
        {
            "extra": "allow",
            "populate_by_name": "True",
            "arbitrary_types_allowed": "True",
        },
    )


class StreamViewerListFetch(StreamViewerListFetchBase, table=True):

    __tablename__: str = "stream_viewerlist_fetch"

    fetch_id: UUID = Field(default_factory=uuid4, primary_key=True)

    scanning_session_id: UUID = Field(
        foreign_key="scanning_sessions.id", nullable=False, index=True
    )
    channel_owner_id: Annotated[
        int,
        Field(
            foreign_key="twitch_user_data.twitch_account_id",
            nullable=False,
            index=True,
        ),
    ]
    category_id: Annotated[
        int,
        Field(
            foreign_key="stream_categories.category_id",
            nullable=False,
            index=True,
        ),
    ]


class StreamViewerListFetchCreate(StreamViewerListFetchBase):
    """Model for creating a new Stream Viewer List Fetch entry."""


class StreamViewerListFetchRead(StreamViewerListFetch):
    """Model for returning Stream Viewer List Fetch data."""
