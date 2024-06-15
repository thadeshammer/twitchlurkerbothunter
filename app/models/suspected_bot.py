# app/models/suspect.py

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, relationship

from app.db import Base


class SuspectedBot(Base):
    __tablename__ = "suspects"

    # TODO should this have a scanning_session_id foreign-keyed in it?
    # TODO should this have a last sighting timestamp? would that be the viewerlist fetch timestamp?

    suspected_bot_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    twitch_account_id = Column(
        BigInteger, ForeignKey("twitch_user_data.twitch_account_id"), nullable=False
    )

    viewer_name = Column(String(40), nullable=False)  # TODO I think we can make this FK
    aliases: Mapped[list] = Column(JSON, default=[])

    account_creation_date = Column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    account_age_in_days = Column(Integer, nullable=False)
    follower_count = Column(Integer, nullable=False)
    following_count = Column(Integer, nullable=False)
    is_banned_or_deleted = Column(Boolean, nullable=False, default=False)

    additional_notes = Column(Text, nullable=True)
    # TODO a field for 'suspicion reason' i.e. a StrEnum from/for the Classifier

    twitch_user_data = relationship("TwitchUserData", back_populates="suspected_bot")
