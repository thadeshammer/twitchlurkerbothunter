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
from typing import TYPE_CHECKING, Optional

from pydantic import conint, constr
from sqlmodel import Field, Relationship, SQLModel

# Stream categories can be left unset by the streamer, either on purpose or by accident.
NO_CATEGORY_ID: int = -1
NO_CATEGORY_NAME: str = "category unset"


class StreamCategoryBase(SQLModel):
    """Base model for StreamCategory with shared properties."""

    category_id: conint(ge=-1) = Field(
        default=NO_CATEGORY_ID, primary_key=True, alias="game_id"
    )
    category_name: constr(max_length=40) = Field(
        default=NO_CATEGORY_NAME, alias="game_name", index=True
    )

    class Config:
        extra = "allow"


class StreamCategory(StreamCategoryBase, table=True):
    """A table to track encountered Twitch categories for easy cross-referencing in our queries.

    Args:
        category_id (int): Twitch's UID for this category.
        category_name (str): The US English (EN) localization of this category's name, limited to 25
            characters.

    Relationships:
        streams_viewerlist_fetch: one-to-one
    """

    __tablename__: str = "stream_categories"

    # relationship
    if TYPE_CHECKING:
        from . import StreamViewerListFetch

    # stream_viewerlist_fetch: Optional["StreamViewerListFetch"] = Relationship(
    #     back_populates="stream_category"
    # )


class StreamCategoryCreate(StreamCategoryBase):
    """Pydantic model to create a new db row for this category."""

    class Config:
        populate_by_name = True


class StreamCategoryRead(StreamCategoryBase):
    """Pydantic model to read a db row for this category."""

    class Config:
        populate_by_name = True
