# app/models/secrets.py
from typing import Union

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text

from app.db import Base


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True)
    access_token = Column(String(512), nullable=False)
    refresh_token = Column(String(512), nullable=False)
    expires_in = Column(Integer, nullable=False)
    token_type = Column(String(64), nullable=False)
    scope = Column(Text, nullable=False)

    def __init__(self, access_token, refresh_token, expires_in, token_type, scope):
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
