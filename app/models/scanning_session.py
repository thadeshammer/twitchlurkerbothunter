from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class ScanningSession(Base):
    __tablename__ = "scanning_sessions"

    scanning_session_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid4())
    )

    time_started = Column(DateTime, nullable=False)
    time_ended = Column(DateTime, nullable=False)

    # channel viewerlists fetched / channels_in_scan ratio metric
    channels_in_scan = Column(Integer, nullable=False)
    viewerlists_fetched = Column(Integer, nullable=False)
    average_time_in_channel = Column(Float, nullable=True)

    error_count = Column(Integer, nullable=True)
    suspects_spotted = Column(Integer, nullable=True)

    channel_viewer_list_fetch = relationship(
        "ChannelViewerListFetch", back_populates="scanning_session"
    )

    # for later
    # resource usage
    # reliability rate of fetches working
