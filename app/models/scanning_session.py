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
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from pydantic import confloat, conint
from sqlmodel import Field, Relationship, SQLModel


class ScanningSessionStopReasonEnum(StrEnum):
    UNSPECIFIED = "unspecified"  # Either in progress or it bombed <_<
    COMPLETE = "complete"  # Hopefully this is as obvious as I want it to be.
    CANCELLED = "cancelled"  # OPERATOR cancellation
    ERRORED = "errored"  # A recoverable but scan-killing error occurred.


class ScanningSessionBase(SQLModel):
    time_started: datetime = Field(...)
    time_ended: Optional[datetime] = Field(None)
    # reason_ended: ScanningSessionStopReasonEnum = Field(
    #     default=ScanningSessionStopReasonEnum.UNSPECIFIED
    # )
    streams_in_scan: conint(gt=0) = Field(...)
    viewerlists_fetched: Optional[conint(ge=0)] = Field(None)
    average_time_per_fetch: Optional[confloat(ge=0)] = Field(None)
    average_time_for_get_user_call: Optional[confloat(ge=0)] = Field(None)
    average_time_for_get_stream_call: Optional[confloat(ge=0)] = Field(None)
    suspects_spotted: Optional[conint(ge=0)] = Field(None)
    error_count: Optional[conint(ge=0)] = Field(None)


class ScanningSession(ScanningSessionBase):
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

    __tablename__: str = "scanning_sessions"

    scanning_session_id: UUID = Field(default_factory=uuid4, primary_key=True)

    if TYPE_CHECKING:
        from . import StreamViewerListFetch

    # stream_viewerlist_fetches: list["StreamViewerListFetch"] = Relationship(
    #     back_populates="scanning_session"
    # )


class ScanningSessionCreate(ScanningSessionBase):
    """Pydantic model for creating a new ScanningSession entry."""


class ScanningSessionRead(ScanningSessionBase):
    """Pydantic model for returning ScanningSession data."""

    scanning_session_id: UUID
