# /app/models/stream_categories.py
"""
StreamCategory

A simple table mapping streaming category ID ('game_id') to name ('game_name').

NOTE In the 'Get Stream' endpoint response, the category name is'game_name' but still includes
categories such as "Art" and "Just Chatting"

Classes:
    StreamCategory: The SQLAlchemy model for this table.
    StreamCategoryAPIResponse: The Pydantic BaseModel for validation.
    StreamCategoryCreate and StreamCategoryRead: Pydantic create and read classes.
"""
from sqlalchemy import BigInteger, Column, Index, String
from sqlalchemy.orm import relationship

from app.db import Base

# Stream categories can be left unset by the streamer, either on purpose or by accident.
NO_CATEGORY_ID: int = -1
NO_CATEGORY_NAME: str = "category unset"


class StreamCategory(Base):
    """A table to track encountered Twitch categories for easy cross-referencing in our queries.

    Args:
        category_id (int): Twitch's UID for this category.
        category_name (str): The US English (EN) localization of this category's name, limited to 25
            characters.

    Relationships:
        streams_viewerlist_fetch: one-to-one
    """

    __tablename__ = "stream_categories"

    category_id = Column(
        BigInteger, primary_key=True, default=NO_CATEGORY_ID, autoincrement=False
    )
    category_name = Column(
        String(40), unique=True, nullable=False, default=NO_CATEGORY_NAME, index=True
    )

    # relationship
    stream_viewerlist_fetch = relationship(
        "StreamViewerListFetch", back_populates="stream_category"
    )
