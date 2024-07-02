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

    TwitchUserDataFromGetStreamAPIResponse: If this is the first we've seen a login name (i.e. we've
    only seem then once and they were streaming) this call is used to create a partial entry on this
    table.
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, Optional, cast

from pydantic import conint, constr, model_validator
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel._compat import SQLModelConfig

from ._validator_regexes import TWITCH_LOGIN_NAME_REGEX


class TwitchAccountTypeValues(str, Enum):
    # ["staff", "admin", "global_mod", ""]
    STAFF = "staff"
    ADMIN = "admin"
    GLOBAL_MOD = "global_mod"
    NORMAL = ""


class TwitchBroadcasterType(str, Enum):
    # ["partner", "affiliate", ""]
    PARTNER = "partner"
    AFFILIATE = "affiliate"
    NORMAL = ""


class TwitchUserDataBase(SQLModel, table=False):
    """SQLmodel representing Twitch Users that have been spotted during scans.

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

    twitch_account_id: conint(gt=0) = Field(..., index=True, primary_key=True)
    login_name: constr(pattern=TWITCH_LOGIN_NAME_REGEX) = Field(..., index=True)
    account_type: Optional[TwitchAccountTypeValues] = Field(default=None, nullable=True)
    broadcaster_type: Optional[TwitchBroadcasterType] = Field(
        default=None, nullable=True
    )
    lifetime_view_count: Optional[int] = Field(default=None, nullable=True)
    account_created_at: Optional[datetime] = Field(default=None)

    first_sighting_as_viewer: Optional[datetime] = Field(default=None)
    most_recent_sighting_as_viewer: Optional[datetime] = Field(default=None)
    most_recent_concurrent_channel_count: Optional[int] = Field(default=None)
    all_time_high_concurrent_channel_count: Optional[int] = Field(default=None)
    all_time_high_at: Optional[datetime] = Field(default=None)

    @model_validator(mode="before")
    def handle_aliasing(cls, data: dict[str, Any]):
        """Handle multiple aliases.

        In Pydantic V1, coupling Field(alias=) and Config's populate_by_name would allow me to push
        in several different formats for this data with only one class to worry about handling it.
        For example:
            - twitch_login_id <- 'id' in 'Get User' response
            - twitch_login_id <- 'user_id' in 'Get Stream' response
            - twitch_login_id would still map to itself

        Pydantic V2 this is documented to be inconsistent and there's plans to address this in V3.
        See: https://github.com/pydantic/pydantic/issues/8379

        So for now we'll handle it manually here, manually fingerprinting each response and
        converting accordingly.
        """
        if all(
            key in data for key in ["user_id", "user_login", "game_id", "game_name"]
        ):
            # 'Get Streams' fingerprint
            print(f"TwitchUserData from Get Streams: {data}")
            data["twitch_account_id"] = data.pop("user_id")
            data["login_name"] = data.pop("user_login")
        elif all(key in data for key in ["id", "login", "type", "broadcaster_type"]):
            # 'Get Users' fingerprint
            print(f"TwitchUserData from Get Users: {data}")
            data["twitch_account_id"] = data.pop("id")
            data["login_name"] = data.pop("login")
            data["account_type"] = data.pop("type")
            data["lifetime_view_count"] = data.pop("view_count")
            data["account_created_at"] = data.pop("created_at")

    model_config = cast(
        SQLModelConfig,
        {"extra": "allow"},
    )


class TwitchUserData(TwitchUserDataBase, table=True):
    """Table model for TwitchUserData with additional fields and relationships."""

    __tablename__: str = "twitch_user_data"

    # Relationships
    # if TYPE_CHECKING:
    #     from . import StreamViewerListFetch, SuspectedBot

    # suspected_bot: Optional["SuspectedBot"] = Relationship(
    #     back_populates="twitch_user_data"
    # )
    # stream_viewerlist_fetch: Optional["StreamViewerListFetch"] = Relationship(
    #     back_populates="twitch_user_data"
    # )


class TwitchUserDataCreate(TwitchUserDataBase):
    """Model for creating a new TwitchUserData entry."""


class TwitchUserDataRead(TwitchUserDataBase):
    """Model for reading TwitchUserData from the db."""


# TODO cut this if the constructor works
# class TwitchUserDataCreateFromStreamsAPIResponse(SQLModel):
#     """Base model for user creation from the StreamViewerListFetcher."""

#     twitch_account_id: conint(gt=0) = Field(..., alias="user_id")
#     login_name: constr(pattern=TWITCH_LOGIN_NAME_REGEX) = Field(..., alias="user_login")

#     class Config:
#         extra = "allow"
