from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import relationship

from app.db import Base


class StreamCategory(Base):
    __tablename__ = "stream_categories"

    category_id = Column(BigInteger, primary_key=True)
    category_name = Column(String(40), nullable=False)  # in en

    streams_viewerlist_fetch = relationship(
        "StreamViewerListFetch",
        back_populates="stream_categories",
    )
