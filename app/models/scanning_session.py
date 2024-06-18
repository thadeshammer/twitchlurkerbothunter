from enum import StrEnum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class ScanningSessionStopReasonEnum(StrEnum):
    UNSPECIFIED = "unspecified"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERRORED = "errored"


class ScanningSession(Base):
    __tablename__ = "scanning_sessions"

    scanning_session_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid4())
    )

    time_started = Column(DateTime, nullable=False)
    time_ended = Column(DateTime, nullable=True)
    reason_ended = Column(
        String(12), nullable=True, default=ScanningSessionStopReasonEnum.UNSPECIFIED
    )  # ScanningSessionStopReasonEnum

    # channel viewerlists fetched / channels_in_scan ratio metric
    streams_in_scan = Column(Integer, nullable=False)
    viewerlists_fetched = Column(Integer, nullable=True)
    average_time_per_fetch = Column(Float, nullable=True)
    average_time_for_get_user_call = Column(Float, nullable=True)
    average_time_for_get_stream_call = Column(Float, nullable=True)

    suspects_spotted = Column(Integer, nullable=True)
    error_count = Column(Integer, nullable=True)

    stream_viewerlist_fetches = relationship(
        "StreamViewerListFetch", back_populates="scanning_session"
    )  # many stream_viewerlist_fetches to one scanning_session

    # for later
    # resource usage
    # reliability rate of fetches working
