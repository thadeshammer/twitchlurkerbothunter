# app/models/secrets.py
"""
Secret model for the secrets table in the database using SQLAlchemy and Pydantic.

The Secret model is used to store OAuth tokens and their associated metadata, 
ensuring that there is only one set of tokens stored at any given time.

Classes:
    Secret: SQLAlchemy model for the secrets table, defining the schema and 
        initialization of access token, refresh token, expiration time, 
        token type, and scope.
    SecretBase: Pydantic base model for data validation and serialization, 
        containing fields for access token, refresh token, expiration time, 
        token type, and scope.
    SecretCreate: Pydantic model for creating a new Secret, allowing the scope 
        to be either a string or a list of strings.
    SecretPydantic: Pydantic model for serializing the Secret model, including 
        the id field and enabling ORM mode for compatibility with SQLAlchemy.

Modules:
    typing: Provides support for type hints.
    pydantic: Used for data validation and serialization.
    sqlalchemy: Provides the ORM capabilities for the Secret model.
    app.db: Contains the base SQLAlchemy model for the application.
"""

from typing import Union

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text

from app.db import Base


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True)
    enforce_one_row = Column(String(15), unique=True, default="enforce_one_row")
    access_token = Column(String(512), nullable=False)
    refresh_token = Column(String(512), nullable=False)
    expires_in = Column(Integer, nullable=False)
    token_type = Column(String(64), nullable=False)
    scope = Column(Text, nullable=False)

    def __init__(
        self, access_token, refresh_token, expires_in, token_type, scope
    ):  # pylint: disable=R0913
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.scope = scope


class SecretBase(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str


class SecretCreate(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: Union[str, list[str]]


class SecretPydantic(SecretBase):
    id: int

    class Config:
        orm_mode = True
