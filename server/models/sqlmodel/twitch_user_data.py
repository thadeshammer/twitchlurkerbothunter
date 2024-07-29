# server/models/twitch_user_data.py
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
from enum import StrEnum
from typing import Annotated, Any, Optional, cast

from pydantic import BaseModel, StringConstraints, model_validator
from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig

from .._validator_regexes import TWITCH_LOGIN_NAME_REGEX


class TwitchAccountType(StrEnum):
    # ["staff", "admin", "global_mod", ""]
    STAFF = "staff"
    ADMIN = "admin"
    GLOBAL_MOD = "global_mod"
    NORMAL = ""


class TwitchBroadcasterType(StrEnum):
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
        account_created_at (DateTime): Timestamp of this account's creation.

        NOTE. 'view_count': Was depecated two years ago and slated for removal, but it still lingers
        and returns 0 in every request.

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

    twitch_account_id: Annotated[int, Field(..., index=True, primary_key=True, ge=0)]
    login_name: Annotated[
        str, StringConstraints(pattern=TWITCH_LOGIN_NAME_REGEX), Field(..., index=True)
    ]

    # NOTE In the edgecase where we create a a partial row from 'Get Stream' data, these fields
    # below are optional; they'll be updated during enrichment.

    # NOTE. We don't give the DB enums because of these outstanding issue:
    # - https://github.com/pydantic/pydantic-core/issues/1336
    # - https://github.com/pydantic/pydantic/discussions/9270
    account_type: Optional[str] = Field(default=None, nullable=True)
    broadcaster_type: Optional[str] = Field(default=None, nullable=True)
    account_created_at: Optional[datetime] = Field(default=None)

    first_sighting_as_viewer: Optional[datetime] = Field(default=None)
    most_recent_sighting_as_viewer: Optional[datetime] = Field(default=None)
    most_recent_concurrent_channel_count: Annotated[
        Optional[int], Field(default=None, gt=0)
    ]
    all_time_high_concurrent_channel_count: Annotated[
        Optional[int], Field(default=None, gt=0)
    ]
    all_time_high_at: Optional[datetime] = Field(default=None)

    @model_validator(mode="before")
    def validate_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Handle multiple aliases and check enums in 'type' and 'broadcaster_type' if applicable.

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
        if data is None:
            raise ValueError("No data.")

        if not isinstance(data, dict):
            raise TypeError(f"data is {type(data)} but needs be dict.")

        if all(
            key in data for key in ["user_id", "user_login", "game_id", "game_name"]
        ):
            # 'Get Streams' fingerprint
            data["twitch_account_id"] = data.pop("user_id")
            data["login_name"] = data.pop("user_login").lower()
        elif all(key in data for key in ["id", "login", "type", "broadcaster_type"]):
            # 'Get Users' fingerprint
            data["twitch_account_id"] = data.pop("id")
            data["login_name"] = data.pop("login").lower()
            data["account_type"] = data.pop("type")
            data["account_created_at"] = data.pop("created_at")

            if "viewer_count" in data:
                data.pop("viewer_count")

            if not data["account_type"] in TwitchAccountType.__members__.values():
                raise ValueError("Invalid value for account_type enum.")
            if (
                not data["broadcaster_type"]
                in TwitchBroadcasterType.__members__.values()
            ):
                raise ValueError("Invalid value for broadcaster_type enum.")

        return data

    model_config = cast(
        SQLModelConfig,
        {
            "populate_by_name": "True",
            "arbitrary_types_allowed": "True",
        },
    )


class TwitchUserData(TwitchUserDataBase, table=True):
    """Table model for TwitchUserData with additional fields and relationships."""

    __tablename__: str = "twitch_user_data"


class TwitchUserDataCreate(TwitchUserDataBase):
    """Model for creating a new TwitchUserData entry."""


class TwitchUserDataRead(TwitchUserDataBase):
    """Model for reading TwitchUserData from the db."""


class GetUsersResponse(BaseModel):
    """Model for parsing a 'Get Users' response which is a list[dict], where each dict will fall
    into our TwitchUserDataCreate by design."""

    users: list[TwitchUserDataCreate]