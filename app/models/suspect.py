# app/models/suspect.py

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db_base import Base


class Suspect(Base):
    __tablename__ = "suspects"

    twitch_account_id = Column(
        String(255), ForeignKey("twitch_user_data.twitch_account_id"), primary_key=True
    )
    viewer_name = Column(String(255), nullable=False)
    account_creation_date = Column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    age = Column(Integer, nullable=False)
    follower_count = Column(Integer, nullable=False)
    following_count = Column(Integer, nullable=False)
    additional_notes = Column(Text, nullable=True)

    twitch_user_data = relationship("TwitchUserData", back_populates="suspects")


class SuspectBase(BaseModel):
    viewer_name: str
    account_creation_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    age: int
    follower_count: int
    following_count: int
    additional_notes: Optional[str] = None


class SuspectCreate(SuspectBase):
    twitch_account_id: str


class SuspectPydantic(SuspectBase):
    twitch_account_id: str

    class Config:
        orm_mode = True
