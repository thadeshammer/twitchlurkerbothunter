# app/models/twitch_user_data.py

from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, Integer, String
from sqlalchemy.orm import relationship  # type: ignore

from app.db import Base


class TwitchUserData(Base):
    # Twitch Users that have been spotted during scans.
    __tablename__ = "twitch_user_data"

    #
    # 'Get User' response data
    #

    # UID Twitch uses to uniquely identify each account, persists across name changes.
    twitch_account_id = Column(BigInteger, primary_key=True)  # 'id'

    # Unique, all lowercase: used for auth, URLs, and Twitch backend API calls.
    login_name = Column(String(40), nullable=False)  # 'login'

    # Varying capitalization and can include non-Latin characters for internationalization.
    display_name = Column(String(40), nullable=False)  # 'display_name'

    # Account type, values: ('staff', 'admin', 'global_mod', '') where '' is a normal user.
    account_type = Column(String(15), nullable=True)  # 'type'

    # Broadcaster type: ('partner', 'affiliate', '') where '' is a normal user.
    broadcaster_type = Column(String(15), nullable=True)  # 'broadcaster_type'

    # Description: about section bio, max 300 characters
    # NOT STORED

    # NOT STORED: 'description', 'profile_image_url', and 'offline_image_url'
    # IF we want these for display purposes, we can 'Get User' at the time for visualization.

    #
    # Collected data
    #
    most_recent_concurrent_channel = Column(Integer, nullable=False)
    all_time_concurrent_channels = Column(Integer, nullable=False)

    # Relationships
    # One-or-none / optional one-to-one with SuspectedBot table.
    suspected_bot = relationship(
        "SuspectedBot", uselist=False, back_populates="twitch_user_data"
    )
    # TODO should this model have a Bool for is_suspect? or otherwise link to suspect entries?


class TwitchUserDataBase(BaseModel):
    login_name: str
    display_name: str
    most_recent_concurrent_channel: int
    all_time_concurrent_channels: int
    is_banned_or_deleted: bool
    aliases: list[str]


class TwitchUserDataCreate(TwitchUserDataBase):
    twitch_account_id: str


class TwitchUserDataPydantic(TwitchUserDataBase):
    twitch_account_id: str

    class Config:
        orm_mode = True
