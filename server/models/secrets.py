# server/models/secrets.py
# SQLAlchemy Base model for access and refresh tokens, and their associated metadata and TTL.
"""
A table for storing some short-lived secrets.

The Secret table is used to store OAuth tokens and their associated metadata, which the app uses for
its Twitch API interactions (the same access token is used both for IRC interactions and Helix).

It ensures that there is only one set of tokens stored at any given time using the unique column
entry constraint trick.

Classes:
    Secret: SQLAlchemy model for the secrets table, defining the schema and initialization of access
        token, refresh token, expiration time, token type, and scope.
    SecretBase: Pydantic base model for data validation and serialization, containing fields for
        access token, refresh token, expiration time, token type, and scope.
    SecretCreate: Pydantic model for creating a new Secret, allowing the scope to be either a string
        or a list of strings.
    SecretRead: Pydantic model for serializing the Secret model, including the id field and
        enabling ORM mode for compatibility with SQLAlchemy.
"""
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, Union

from pydantic import StringConstraints, model_validator
from sqlmodel import Field, SQLModel

from ._validator_regexes import TWITCH_TOKEN_REGEX


class TokenType(StrEnum):
    BEARER = "bearer"


class SecretBase(SQLModel):
    access_token: Annotated[
        str, StringConstraints(max_length=512, pattern=TWITCH_TOKEN_REGEX), Field(...)
    ]
    refresh_token: Annotated[
        str, StringConstraints(max_length=512, pattern=TWITCH_TOKEN_REGEX), Field(...)
    ]
    expires_in: int = Field(..., gt=0)
    token_type: str = Field(...)  # usually "bearer" but irrelevant, really
    scope: Annotated[
        str, StringConstraints(min_length=7), Field(...)
    ]  # space-delimited


class Secret(SecretBase, table=True):
    """Single-row table to store short-lived oauth tokens and associated metadata. Uses
    unique/default combo to enforce there being only one row.

    Args:
        Base (_type_): _description_
        id (int): I think this will literally always be 1. Do I need this? Probably not.
        enforce_one_row (str): Uses the classic unique/default combo to ensure only one table row.
        access_token (str): Twitch OAuth access token for API interactions.
        refresh_token (str): Twitch OAuth refresh token; get a new access token after expiry.
        expires_in (int): Time in seconds until the access token expires.
        token_type (str): Docs say this is almost always "bearer".
        scope (str or list[str]): One or more scopes that spec out how much we can access with the
            token. NOTE I went with 'scope' to be consistent with the API response lingo.
        last_update_timestamp (DateTime): The timestamp of the last time this row was updated.

    """

    __tablename__: str = "secrets"

    id: int = Field(default=None, primary_key=True)
    enforce_one_row: str = Field(default="enforce_one_row", unique=True, nullable=False)
    last_update_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class SecretCreate(SecretBase):
    @model_validator(mode="before")
    def validate_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        assert "token_type" in data
        assert data["token_type"] in TokenType.__members__.values()

        assert "scope" in data and data["scope"] is not None
        if isinstance(data["scope"], list):
            # This will be a VERY small number of scopes, usually one, at most three.
            data["scope"] = " ".join(data["scope"])

        return data


class SecretRead(SecretBase):
    id: int
    last_update_timestamp: datetime
