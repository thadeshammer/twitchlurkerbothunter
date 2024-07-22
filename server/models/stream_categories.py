# server/models/stream_categories.py
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
from typing import Annotated, Any, cast

from pydantic import StringConstraints, model_validator
from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig

# Stream categories can be left unset by the streamer, either on purpose or by accident.
NO_CATEGORY_ID: int = -1
NO_CATEGORY_NAME: str = "category unset"


class StreamCategoryBase(SQLModel):
    """Base model for StreamCategory with shared properties."""

    category_id: Annotated[
        int, Field(default=NO_CATEGORY_ID, primary_key=True, ge=NO_CATEGORY_ID)
    ]  #  alias="game_id",
    category_name: Annotated[
        str,
        StringConstraints(max_length=40),
        Field(default=NO_CATEGORY_NAME, index=True),
    ]  # alias="game_name",

    @model_validator(mode="before")
    def handle_aliases(cls, data: dict[str, Any]) -> dict[str, Any]:
        if all(x in data for x in ["game_id", "game_name"]):
            data["category_id"] = data.pop("game_id")
            data["category_name"] = data.pop("game_name")
        elif all(x in data for x in ["box_art_url", "igdb_id"]):
            data["category_id"] = data.pop("id")
            data["category_name"] = data.pop("name")
        return data

    model_config = cast(
        SQLModelConfig,
        {
            "populate_by_name": "True",
            "arbitrary_types_allowed": "True",
        },
    )


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


class StreamCategoryCreate(StreamCategoryBase):
    """Pydantic model to create a new db row for this category."""


class StreamCategoryRead(StreamCategoryBase):
    """Pydantic model to read a db row for this category."""
