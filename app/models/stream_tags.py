from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import relationship

from app.db import Base

# Association table for the many-to-many relationship
stream_tags_association = Table(
    "stream_tags_association",
    Base.metadata,
    Column(
        "stream_viewer_list_fetch_id",
        String(36),
        ForeignKey("stream_viewer_list_fetch.fetch_id"),
    ),
    Column("tag_id", String(36), ForeignKey("stream_tags.tag_id")),
)


class StreamTag(Base):
    __tablename__ = "stream_tags"
    tag_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

    streams_relationship = relationship(
        "StreamViewerListFetch",
        secondary=stream_tags_association,
        back_populates="tags_relationship",
    )
