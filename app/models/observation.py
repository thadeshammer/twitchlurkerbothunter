# app/models/observation.py

from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class Observation(Base):
    __tablename__ = "observations"

    observation_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    twitch_account_id = Column(
        String(255), ForeignKey("twitch_user_data.twitch_account_id"), nullable=False
    )
    viewer_name = Column(String(255), nullable=False)
    channel_id = Column(String(255), nullable=False)
    channel_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    viewer_count = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    # Relationships
    twitch_user_data = relationship("TwitchUserData", back_populates="observations")


class ObservationBase(BaseModel):
    viewer_name: str
    channel_id: str
    channel_name: str
    category: str
    viewer_count: int
    processing_time: float
    timestamp: str


class ObservationCreate(ObservationBase):
    twitch_account_id: str


class ObservationPydantic(ObservationBase):
    observation_id: str
    twitch_account_id: str

    class Config:
        orm_mode = True
