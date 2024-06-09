from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped

from server.db import Base


class TestModel(Base):  # type: ignore
    __tablename__ = 'test_table'

    id: Mapped[int] = Column(Integer,
                             primary_key=True,
                             autoincrement=True,
                             index=True)
    uid: Mapped[str] = Column(String, unique=True)
    name: Mapped[str] = Column(String, index=True)


class TestData(BaseModel):
    uid: str
    name: str
