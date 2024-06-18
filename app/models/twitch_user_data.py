# app/models/twitch_user_data.py
# SQLAlchemy model representing Twitch Users that have been spotted during scans.
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class TwitchUserData(Base):
    """SQLAlchemy model representing Twitch Users that have been spotted during scans.

    Attributes from 'Get User' Twitch backend API endpoint:
        twitch_account_id (int):the UID Twitch uses to uniquely
            identify each account, persists across name changes.
        login_name (str): Unique, all lowercase: used for auth, URLs, and Twitch backend API calls.
        display_name (str): The login_name with varying capitalization, and can include non-Latin
            characters for internationalization.
        account_type (str): Possible values: ('staff', 'admin', 'global_mod', '') where '' is a
            normal user.
        broadcaster_type (str): Possible values: ('partner', 'affiliate', '') where '' is a normal
            user.

        NOTE. We're not currently storing 'description' or profile_img urls. If we want these for
            display purposes / visualization, we can fetch them adhoc or reconsider later.

    Attributes from our data collection.
        most_recent_concurrent_channel (int): Count of channels this account was observed to be in
            during the most recent scan it was seen in.
        most_recent_sighting (DateTime): Timestamp of the last time this user was observed during a
            scan.
        all_time_concurrent_channels (int): The highest count of channels this account_id was ever
            observed in across all scans it's been a part of.
        all_time_high_at (DateTime): Timestamp of the all_time_concurrent_channels reading.

    Relationships:
        suspected_bot
    """

    __tablename__ = "twitch_user_data"

    twitch_account_id = Column(BigInteger, primary_key=True)  # 'id'
    login_name = Column(String(40), unique=True, nullable=False)  # 'login'
    display_name = Column(String(40), unique=True, nullable=False)  # 'display_name'
    account_type = Column(String(15), nullable=False)  # 'type'
    broadcaster_type = Column(String(15), nullable=False)  # 'broadcaster_type'
    lifetime_view_count = Column(Integer, nullable=False)  # 'view_count'
    account_created_at = Column(DateTime, nullable=False)  # 'created_at'

    # not tracking: description, image urls, email,

    # Collected data
    # NOTE Could FK in scanning_session_id for most_recent sighting AND first_sighting BUT those
    # tables will grow pretty quickly and may be subject to pruning.
    first_sighting_as_viewer = Column(DateTime, nullable=False)
    most_recent_sighting_as_viewer = Column(DateTime, nullable=False)
    most_recent_concurrent_channel_count = Column(Integer, nullable=False)
    all_time_high_concurrent_channel_count = Column(Integer, nullable=False)
    all_time_high_at = Column(DateTime, nullable=False)
    suspected_bot_id = Column(
        CHAR(36), ForeignKey("suspected_bots.suspected_bot_id"), nullable=True
    )

    # Relationships
    stream_viewerlist_fetch = relationship(
        "StreamViewerlistFetch", back_populates="twitch_user_data"
    )

    # One-or-none / optional one-to-one with SuspectedBot table.
    suspected_bot = relationship(
        "SuspectedBot", uselist=False, back_populates="twitch_user_data"
    )

    # indexes
    __table_args__ = (
        Index("ix_twitch_account_id", "twitch_account_id"),
        Index("ix_login_name", "login_name"),
        Index("ix_suspected_bot_id", "suspected_bot_id"),
    )
