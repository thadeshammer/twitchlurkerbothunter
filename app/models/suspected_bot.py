# app/models/suspect.py

from datetime import datetime, timezone
from enum import StrEnum
from typing import Tuple
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class SuspicionReason(StrEnum):
    UNSPECIFIED = "unspecified"
    CONCURRENT_CHANNEL_COUNT = "concurrent_channel_count"


class SuspicionLevel(StrEnum):
    RED = "red"  # 100001+ channels (Highest alert)
    ORANGE = "orange"  #  50001 - 100k channels
    YELLOW = "yellow"  #  10001 - 50k channels
    GREEN = "green"  #   1001 - 10k channels
    BLUE = "blue"  #    101 - 1k channels
    PURPLE = "purple"  #     21 - 100 channels, technically within TOS for even unapproved bots.
    GRAY = "gray"  #     11 - 20 channels (Lowest alert, Moonu Level)
    NONE = "none"  #      1 - 10 channels


SUSPICION_RANKING_THRESHOLDS: dict[Tuple[int, int], SuspicionLevel] = {
    (100001, 9999999): SuspicionLevel.RED,
    (50001, 100000): SuspicionLevel.ORANGE,
    (10001, 50000): SuspicionLevel.YELLOW,
    (1001, 10000): SuspicionLevel.GREEN,
    (101, 1000): SuspicionLevel.BLUE,
    (21, 100): SuspicionLevel.PURPLE,
    (11, 20): SuspicionLevel.GRAY,
    (1, 10): SuspicionLevel.NONE,
}


class SuspectedBot(Base):
    __tablename__ = "suspects"

    # TODO should this have a scanning_session_id foreign-keyed in it?
    # TODO should this have a last sighting timestamp? would that be the viewerlist fetch timestamp?

    suspected_bot_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))

    # Foreign Keys
    twitch_account_id = Column(
        BigInteger,
        ForeignKey("twitch_user_data.twitch_account_id"),
        unique=True,
        nullable=False,
    )

    account_creation_date = Column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    account_age_in_days = Column(Integer, nullable=False)
    follower_count = Column(Integer, nullable=False)
    following_count = Column(Integer, nullable=False)
    is_banned_or_deleted = Column(Boolean, nullable=False, default=False)

    suspicion_level = Column(String(8), default=SuspicionLevel.NONE)
    suspicion_reason = Column(String(30), default=SuspicionReason.UNSPECIFIED)
    additional_notes = Column(Text, nullable=True)

    # relationships
    twitch_user_data = relationship("TwitchUserData", back_populates="suspected_bot")

    # indexes
    __table_args__ = Index("ix_twitch_account_id", "twitch_account_id")
