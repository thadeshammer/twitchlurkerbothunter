# app/models/twitch_user_data.py

from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, Integer, String
from sqlalchemy.orm import relationship  # type: ignore

from app.db import Base


class TwitchUserData(Base):
    __tablename__ = "twitch_user_data"

    twitch_account_id = Column(BigInteger, primary_key=True)
    viewer_name = Column(String(40), nullable=False)
    total_channels_spotted = Column(Integer, nullable=False)
    max_concurrent_channels = Column(Integer, nullable=False)

    # Relationships
    suspected_bot = relationship("SuspectedBot", back_populates="twitch_user_data")
    # TODO should this model have a Bool for is_suspect? or otherwise link to suspect entries?


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
