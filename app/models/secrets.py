# app/models/secrets.py
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
from enum import StrEnum
from typing import Union

from pydantic import BaseModel, Field, conint, constr
from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.db import Base

from ._validator_regexes import TWITCH_TOKEN_REGEX


class TokenType(StrEnum):
    BEARER = "bearer"


class Secret(Base):
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
            token.
        last_update_timestamp (DateTime): The timestamp of the last time this row was updated.

    """

    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True)
    enforce_one_row = Column(String(15), unique=True, default="enforce_one_row")
    access_token = Column(String(512), nullable=True)
    refresh_token = Column(String(512), nullable=True)
    expires_in = Column(Integer, nullable=True)
    token_type = Column(String(64), nullable=True)
    scope = Column(Text, nullable=True)

    # For calculating and tracking TTL and when to use refresh token
    last_update_timestamp = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )


class SecretBase(BaseModel):
    access_token: constr(max_length=512, regex=TWITCH_TOKEN_REGEX) = Field(...)
    refresh_token: constr(max_length=512, regex=TWITCH_TOKEN_REGEX) = Field(...)
    expires_in: conint(gt=0) = Field(...)
    token_type: TokenType = Field(...)
    scope: Union[str, list[str]] = Field(..., alias="scope")


class SecretCreate(SecretBase):
    pass


class SecretRead(SecretBase):
    id: conint(gt=0)

    class Config:
        orm_mode = True
