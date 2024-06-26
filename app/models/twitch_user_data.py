# app/models/twitch_user_data.py
# SQLAlchemy model representing Twitch Users that have been spotted during scans.
"""
TwitchUserData

SQLAlchemy models and Pydantic machinery (validation and serializing) for the twitch_user_data
table. Each row represnts a Twitch User that has been spotted during a scan at least once, keeping
track of user metadata and metrics. Many tables in the data model FK to twitch_account_id on this
table, as it's a UID for a user on the Twitch platform.

This model does NOT track user email (which it does not request) or name changes (which it ignores).

Usage:

    From 'Get User' use TwitchUserDataAPIResponse and TwitchUserDataAppData, then call the merge
    function to make a Create model for commit to the DB.

Classes:

    TwitchUserData: The SQLAlchemy model.
    TwitchUserDataAPIResponse: Pydantic BaseModel to serialize the API response.
    TwitchUserDataAppData: Pydantic BaseModel to serialize this app's associated metadata for this
    user. 
    TwitchUserDataCreate and Read: Pydantic models to create for and read from the DB respectively.

    merge_twitch_user_data: Helper method to combine APIResponse and AppData. NOTE don't use this
    when creating from the GetStream response via the StreamViewerListFetch action.

    TwitchUserDataFromGetStreamAPIResponse: If this is the first we've seen a login name (i.e. we've
    only seem then once and they were streaming) this call is used to create a partial entry on this
    table.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Extra, Field, conint, constr, validator
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

from ._validator_regexes import TWITCH_LOGIN_NAME_REGEX


class TwitchUserData(Base):
    """SQLAlchemy model representing Twitch Users that have been spotted during scans.

    NOTE. This wound up being mostly nullable due to a critical edge case: if a streamer is first
    observed when they're streaming, the creation of the associated StreamViewerListFetch table row
    will require a FK connection to this table via their login ID number. We'll have that (it comes
    in via the 'Get Stream' API response) but we won't have the rest of their metadata which we get
    via 'Get User'. The 'Get User' call will happen later in a batch during the regular enrichment
    process (as the streamer will appear in the ViewerSightings table as they're always reported as
    a viewer in their stream).

    NOTE. If I'm wrong and they're not always reported, we'll still get them with routine checks of
    the DB later.

    NOTE. Display Name was dropped from the spec. It's the login_name with varying capitalization,
    and can include non-Latin characters for internationalization and white spaces. This represents
    a LOT of space on the hard drive and doesn't really bring value, at least not during our first
    pass here. Additionally, it would require some fancy custom validation using Python's regex over
    standard re, and since Pydantic only uses re, I'd have to wire it up myself. And also set up
    MySQL for Unicode. File this under "Possible future work."

    Attributes from 'Get Users' Twitch backend API endpoint:
        twitch_account_id (int): the UID Twitch uses to uniquely identify each account, persists
            across name changes.
        has_been_enriched (bool): Whether the User Data Enricher has populated this row with a 'Get
            Users' result.

        login_name (str): Unique, all lowercase: used for auth, URLs, and Twitch backend API calls.
        account_type (str): Possible values: ('staff', 'admin', 'global_mod', '') where '' is a
            normal user.
        broadcaster_type (str): Possible values: ('partner', 'affiliate', '') where '' is a normal
            user.
        lifetime_view_count (int): The total number of channel views this user's channel has.
        account_created_at (DateTime): Timestamp of this account's creation.

        NOTE. We're not currently storing 'description' or profile_img urls. If we want these for
            display purposes / visualization, we can fetch them adhoc or reconsider later.

    Attributes from our data collection.
        first_sighting_as_viewer (DateTime): The first time this account was spotted AS A VIEWER
            during a scanning session.
        most_recent_sighting_as_viewer (DateTime): Timestamp of the last time this user was observed
            during a scan AS A VIEWER.
        most_recent_concurrent_channel_count (int): Count of channels this account was observed to
            be in during the most recent scan it was seen in.
        all_time_high_concurrent_channel_count (int): The highest count of channels this account_id
            was ever observed in across all scans it's been a part of.
        all_time_high_at (DateTime): Timestamp of the all_time_concurrent_channel_count reading.
    """

    __tablename__ = "twitch_user_data"

    # These core fields are not nullable because they're here at row creation and required.

    twitch_account_id = Column(
        BigInteger, primary_key=True, autoincrement=False
    )  # 'id'
    has_been_enriched = Column(Boolean, default=False)

    # In the specific case where first contact with a login name is a streamer who's live, their
    # entry here will be created prior to the enrichment pass over ViewerSightings. So these need to
    # be nullable to account for that.
    login_name = Column(String(40), unique=True, nullable=False)  # 'login'
    account_type = Column(String(15), nullable=True)  # 'type'
    broadcaster_type = Column(String(15), nullable=True)  # 'broadcaster_type'
    lifetime_view_count = Column(Integer, nullable=True)  # 'view_count'
    account_created_at = Column(DateTime, nullable=True)  # 'created_at'

    # not tracking: description, image urls, email,

    # Collected data
    # NOTE Could FK in scanning_session_id for most_recent sighting AND first_sighting BUT those
    # tables will grow pretty quickly and may be subject to pruning.

    # These columns will be populated post creation by an aggregator worker, thus they're nullable.

    first_sighting_as_viewer = Column(DateTime, nullable=True)
    most_recent_sighting_as_viewer = Column(DateTime, nullable=True)
    most_recent_concurrent_channel_count = Column(Integer, nullable=True)
    all_time_high_concurrent_channel_count = Column(Integer, nullable=True)
    all_time_high_at = Column(DateTime, nullable=True)

    # Relationships
    suspected_bot = relationship(
        "SuspectedBot", back_populates="twitch_user_data", uselist=False
    )

    stream_viewerlist_fetch = relationship(
        "StreamViewerListFetch", back_populates="twitch_user_data"
    )

    # indexes
    __table_args__ = (
        Index("ix_twitch_account_id", "twitch_account_id"),
        Index("ix_login_name", "login_name"),
    )


TwitchAccountTypes = Literal["staff", "admin", "global_mod", ""]
TwitchBroadcasterTypes = Literal["partner", "affiliate", ""]


class TwitchUserDataAPIResponse(BaseModel):
    """Base model for TwitchUserData with shared properties."""

    twitch_account_id: conint(gt=0) = Field(..., alias="id")
    login_name: constr(regex=TWITCH_LOGIN_NAME_REGEX) = Field(..., alias="login")
    account_type: Optional[TwitchAccountTypes] = Field(alias="type", default=None)
    broadcaster_type: Optional[TwitchBroadcasterTypes] = Field(default=None)
    lifetime_view_count: Optional[conint(ge=0)] = Field(
        alias="view_count", default=None
    )
    account_created_at: Optional[datetime] = Field(alias="created_at", default=None)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

    @validator("twitch_account_id", "lifetime_view_count", pre=True)
    def str_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v

    @validator("account_created_at", pre=True)
    def str_to_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class TwitchUserDataAppData(BaseModel):
    """Base model for app-generated metrics."""

    first_sighting_as_viewer: Optional[datetime] = Field(None)
    most_recent_sighting_as_viewer: Optional[datetime] = Field(None)
    most_recent_concurrent_channel_count: Optional[conint(gt=0)] = Field(None)
    all_time_high_concurrent_channel_count: Optional[conint(gt=0)] = Field(None)
    all_time_high_at: Optional[datetime] = Field(None)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class TwitchUserDataCreate(TwitchUserDataAPIResponse, TwitchUserDataAppData):
    """Combined API and app data. I can't believe I found a usecase for multiple inheritance."""


class TwitchUserDataRead(TwitchUserDataCreate):
    """Model for the data received from the Twitch API, to be persisted in the db."""


def merge_twitch_user_data(
    api_data: TwitchUserDataAPIResponse,
    app_data: TwitchUserDataAppData,
) -> TwitchUserDataCreate:
    combined_data = {
        **api_data.dict(),
        **app_data.dict(),
    }
    return TwitchUserDataCreate(**combined_data)


# Example API response

# api_response = {
#     "id": 123456,
#     "login": "example_user",
#     "display_name": "ExampleUser",
#     "type": "",
#     "broadcaster_type": "",
#     "view_count": 1000,
#     "created_at": "2013-06-03T19:12:02Z"
# }


class TwitchUserDataFromGetStreamAPIResponse(BaseModel):
    """Base model for user creation from the StreamViewerListFetcher."""

    # https://dev.twitch.tv/docs/api/reference/#get-streams

    twitch_account_id: conint(gt=0) = Field(..., alias="user_id")
    login_name: constr(regex=TWITCH_LOGIN_NAME_REGEX) = Field(..., alias="user_login")

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
        orm_mode = True
