# app/models/test_model.py
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped

from app.db_base import Base


class TestModel(Base):
    __tablename__ = "test_table"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, index=True)
    uid: Mapped[str] = Column(String(255), unique=True)
    name: Mapped[str] = Column(String(255), index=True)


class TestData(BaseModel):
    uid: str
    name: str
