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
from pydantic import BaseModel, Extra, Field, conint, constr
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
        String(40), unique=True, nullable=False, default=NO_CATEGORY_NAME
    )

    # relationship
    stream_viewerlist_fetch = relationship(
        "StreamViewerListFetch", back_populates="stream_category"
    )

    __table_args__ = (Index("ix_category_name", "category_name"),)


class StreamCategoryAPIReponse(BaseModel):
    """Base model for StreamCategory with shared properties."""

    category_id: conint(ge=-1) = Field(..., alias="game_id")
    category_name: constr(max_length=25) = Field(..., alias="game_name")

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
        orm_mode = True


class StreamCategoryCreate(StreamCategoryAPIReponse):
    """Pydantic model to create a new db row for this category."""


class StreamCategoryRead(StreamCategoryAPIReponse):
    """Pydantic model to read a db row for this category."""

    class Config:
        orm_mode = True
