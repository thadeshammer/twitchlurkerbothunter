# /app/models/stream_categories.py
from pydantic import BaseModel, Field, conint, constr
from sqlalchemy import BigInteger, Column, Index, String
from sqlalchemy.orm import relationship

from app.db import Base

# Stream categories can be left unset by the streamer, either on purpose or by accident.
NO_CATEGORY_ID: int = -1
NO_CATEGORY_NAME: str = "category unset"


class StreamCategory(Base):
    """A table to track encountered Twitch categories for easy cross-referencing in our queries.

    NOTE In the 'Get Stream' endpoint response, this is 'game_name' but still includes categories
    such as "Art" and "Just Chatting"

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
        String(40), unique=True, nullable=False, default=NO_CATEGORY_NAME
    )

    streams_viewerlist_fetch = relationship(
        "StreamViewerListFetch",
        back_populates="stream_categories",
    )

    __table_args__ = (Index("ix_category_name", "category_name"),)


class StreamCategoryBase(BaseModel):
    """Base model for StreamCategory with shared properties."""

    category_id: conint(ge=-1) = Field(..., alias="game_id")
    category_name: constr(max_length=25) = Field(..., alias="game_name")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class StreamCategoryCreate(StreamCategoryBase):
    """Pydantic model to create a new db row for this category."""


class StreamCategoryRead(StreamCategoryBase):
    """Pydantic model to read a db row for this category."""

    class Config:
        orm_mode = True
