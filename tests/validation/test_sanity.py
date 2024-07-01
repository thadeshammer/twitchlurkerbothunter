import pytest
from pydantic import BaseModel, ValidationError, field_validator
from sqlmodel import Field, SQLModel


class CheckBaseModel(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


class CheckModel(SQLModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


class CheckModelWithFieldAttrib(SQLModel):
    name: str = Field(...)

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


def test_base_model():
    CheckBaseModel(name="hello")

    with pytest.raises((ValidationError, ValueError)):
        CheckBaseModel(name=123)


def test_sqlmodel():
    CheckModel(name="ohai")

    with pytest.raises((ValidationError, ValueError)):
        CheckModel(name=321)


def test_sqlmodel_with_attributes():
    CheckModelWithFieldAttrib(name="ohai")

    with pytest.raises((ValidationError, ValueError)):
        CheckModelWithFieldAttrib(name=321)
