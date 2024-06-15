# app/models/channel_viewerlist_fetch.py
# A channel_viewerlist_fetch represents the reception of the 353 message.
# For our purposes, it is a set of ViewerSightings in a given Channel during a Sweep.

from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.db import Base


class ChannelViewerListFetch(Base):
    __tablename__ = "channel_viewerlist_fetch"

    fetch_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))

    # channel meta data we're interested in
    channel_id = Column(BigInteger, nullable=False)
    channel_name = Column(String(40), nullable=False)
    category = Column(String(40), nullable=False)

    time_of_fetch = Column(DateTime, nullable=False)
    viewer_count = Column(Integer, nullable=False)
    time_in_channel = Column(
        Float, nullable=False
    )  # use time.perf_counter() to measure, returns fractional seconds

    sweep_id = Column(CHAR(36), ForeignKey("sweeps.sweep_id"), nullable=False)

    sweep = relationship("Sweep", back_populates="channel_viewerlist_fetches")
    viewer_sightings = relationship(
        "ViewerSighting", back_populates="channel_viewerlist_fetch"
    )
