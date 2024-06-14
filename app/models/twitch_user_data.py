# app/models/twitch_user_data.py

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy.orm import Mapped, relationship  # type: ignore

from app.db import Base


class TwitchUserData(Base):
    __tablename__ = "twitch_user_data"

    twitch_account_id = Column(String(255), primary_key=True)
    viewer_name = Column(String(255), nullable=False)
    total_channels_spotted = Column(Integer, nullable=False)
    max_concurrent_channels = Column(Integer, nullable=False)
    is_banned_or_deleted = Column(Boolean, nullable=False, default=False)
    aliases: Mapped[list] = Column(JSON, default=[])

    # Relationships
    observations = relationship("Observation", back_populates="twitch_user_data")
    suspects = relationship("Suspect", back_populates="twitch_user_data")


class TwitchUserDataBase(BaseModel):
    viewer_name: str
    total_channels_spotted: int
    max_concurrent_channels: int
    is_banned_or_deleted: bool
    aliases: list[str]


class TwitchUserDataCreate(TwitchUserDataBase):
    twitch_account_id: str


class TwitchUserDataPydantic(TwitchUserDataBase):
    twitch_account_id: str

    class Config:
        orm_mode = True
