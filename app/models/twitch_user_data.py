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
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from marshmallow import EXCLUDE, fields, pre_load
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
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
        login_name (str): Unique, all lowercase: used for auth, URLs, and Twitch backend API calls.
        account_type (str): Possible values: ('staff', 'admin', 'global_mod', '') where '' is a
            normal user.
        broadcaster_type (str): Possible values: ('partner', 'affiliate', '') where '' is a normal
            user.
        lifetime_view_count (int): The total number of channel views this user's channel has.
        account_created_at (DateTime): Timestamp of this account's creation.

        has_been_enriched (bool): Whether the User Data Enricher has populated this row with a 'Get
            Users' result.

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
        BigInteger, primary_key=True, autoincrement=False, index=True
    )  # 'id'

    # In the specific case where first contact with a login name is a streamer who's live, their
    # entry here will be created prior to the enrichment pass over ViewerSightings. So these need to
    # be nullable to account for that.
    login_name = Column(String(40), unique=True, nullable=False, index=True)  # 'login'
    account_type = Column(String(15), nullable=True)  # 'type'
    broadcaster_type = Column(String(15), nullable=True)  # 'broadcaster_type'
    lifetime_view_count = Column(Integer, nullable=True)  # 'view_count'
    account_created_at = Column(DateTime, nullable=True)  # 'created_at'

    has_been_enriched = Column(Boolean, nullable=False, default=False)

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


TwitchAccountTypes = ["staff", "admin", "global_mod", ""]
TwitchBroadcasterTypes = ["partner", "affiliate", ""]


@dataclass
class TwitchUserDataInternal:
    first_sighting_as_viewer: Optional[datetime]
    most_recent_sighting_as_viewer: Optional[datetime]
    most_recent_concurrent_channel_count: Optional[int]
    all_time_high_concurrent_channel_count: Optional[int]
    all_time_high_at: Optional[datetime]


class TwitchUserDataSchema(SQLAlchemySchema):
    """Marshmallow schema. Hand it the API response dict + TwitchUserDatInternal.as_dict to
    serialize to a TwitchUserData SQLAlchemy model to write to the DB.

    NOTE. Marshamallow isn't as flexible as Pydantic in terms of aliasing; "data_key" is an absolute
    so if this isn't being built from an API response, you'll have to convert the keys prior to
    using it.

    Example API response:

    api_response = {
        "id": 123456,
        "login": "example_user",
        "display_name": "ExampleUser",
        "type": "",
        "broadcaster_type": "",
        "view_count": 1000,
        "created_at": "2013-06-03T19:12:02Z"
    }
    """

    class Meta:
        model = TwitchUserData
        load_instance = True
        include_relationships = True
        unknown = EXCLUDE

    twitch_account_id = fields.Integer(required=True, data_key="id")
    login_name = fields.String(
        required=True,
        validate=lambda x: re.match(TWITCH_LOGIN_NAME_REGEX, x) is not None,
        data_key="login",
    )

    account_type = fields.String(
        allow_none=True, validate=lambda x: x in TwitchAccountTypes, data_key="type"
    )
    broadcaster_type = fields.String(
        allow_none=True,
        validate=lambda x: x in TwitchBroadcasterTypes,
        data_key="broadcaster_type",
    )
    lifetime_view_count = fields.Integer(allow_none=True, data_key="view_count")
    account_created_at = fields.DateTime(allow_none=True, data_key="created_at")

    has_been_enriched = fields.Boolean(load_default=False)
    first_sighting_as_viewer = fields.DateTime(allow_none=True)
    most_recent_sighting_as_viewer = fields.DateTime(allow_none=True)
    most_recent_concurrent_channel_count = fields.Integer(allow_none=True)
    all_time_high_concurrent_channel_count = fields.Integer(allow_none=True)
    all_time_high_at = fields.DateTime(allow_none=True)

    @pre_load
    def remove_display_name(self, data, **kwargs):
        if isinstance(data, dict):
            data.pop("display_name", None)
        return data
