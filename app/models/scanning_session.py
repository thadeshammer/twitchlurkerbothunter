# app/models/scanning_session.py
# SQLAlchemy model representing Scans.
"""ScanningSession and associated classes.

A viewerlist fetch is defined to be an action where the viewerlist for a given live stream is
retrieved by the app.

A Scanning Session (or "Scan") is defined to be a set of viewerlist fetches targeting some number of
live streams.

Classes:
    ScanningSessionStopReasonEnum: Enum for categorizing why a given scanning session ended.
    ScanningSession: the SQLAlchemy model for tracking at-a-glance metrics for a given session of
        scanning.
    ScanningSessionAppData, Create, and Read: Pydantic BaseModels for validation and serializing.
"""
from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class ScanningSessionStopReasonEnum(StrEnum):
    UNSPECIFIED = "unspecified"  # Either in progress or it bombed <_<
    COMPLETE = "complete"  # Hopefully this is as obvious as I want it to be.
    CANCELLED = "cancelled"  # OPERATOR cancellation
    ERRORED = "errored"  # A recoverable but scan-killing error occurred.


class ScanningSession(Base):
    """This table stores metrics for independent scanning session.

    A Scan is a series of viewerlist fetches from a (potentially very large) set of live streams.

    Args:
        scanning_session_id (str): UUID for this scanning session.
        time_started (DateTime): The time the scan was commenced.
        time_ended (DateTime): The time the scan ended. Nullable as it will necessarily need to be
            updated after the row's creation.
        reason_ended (ScanningSessionStopReasonEnum): Reason the app specified for the scan ending.
            Default is "unspecified" so that, in the event of a crash, we don't have a null table
            entry. I'll be adding more as different failpoints are discovered.
        streams_in_scan (int): The quantity of streams in the list at the start of the scan.
        viewerlists_fetched (int): The count of viewerlists that have been / were fetched during
            this scanning session.

        NOTE. Timing is measured with time.perf_counter() unless the scale mandates a timestamp.

        average_time_per_fetch (float): The average time it takes the bot to get a viewerlist,
            calculated at the end of the run. I may need to segment this over stream-sizes, but for
            now, it's a single value.
        average_time_for_get_user_call (float): The average round-trip time it takes for a 'Get
            User' API call.
        average_time_for_get_stream_call (float): Average round-trip time for a 'Get Stream' API
            call.
        suspects_spotted (int): The number of accounts encountered that were either promoted to or
            were already on the SuspectedBot table.
        error_count (int): Raw quantity of errors encountered and handled during this scanning
            session.
    """

    __tablename__ = "scanning_sessions"

    scanning_session_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid4())
    )

    time_started = Column(DateTime, nullable=False)
    time_ended = Column(DateTime, nullable=True)
    reason_ended = Column(
        String(12), nullable=False, default=ScanningSessionStopReasonEnum.UNSPECIFIED
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
