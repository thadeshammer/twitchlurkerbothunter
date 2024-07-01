from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError, field_validator
from sqlmodel import Field, SQLModel

from app.models.viewer_sightings import ViewerSightingBase, ViewerSightingCreate


class TestSubject(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


class TestModel(SQLModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


class TestModelWithFieldAttrib(SQLModel):
    name: str = Field(...)

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("nope")
        return v


def test_base_model():
    TestSubject(name="hello")

    with pytest.raises((ValidationError, ValueError)):
        TestSubject(name=123)


def test_sqlmodel():
    TestModel(name="ohai")

    with pytest.raises((ValidationError, ValueError)):
        TestModel(name=321)


def test_sqlmodel_with_attributes():
    TestModelWithFieldAttrib(name="ohai")

    with pytest.raises((ValidationError, ValueError)):
        TestModelWithFieldAttrib(name=321)


def test_viewer_sighting_base():
    ViewerSightingBase(viewer_login_name="howdy", viewerlist_fetch_id=uuid4())

    with pytest.raises((ValidationError, ValueError)):
        ViewerSightingBase(viewer_login_name=123, viewerlist_fetch_id=uuid4())

    with pytest.raises((ValidationError, ValueError)):
        ViewerSightingBase(viewer_login_name="hilo", viewerlist_fetch_id="no")


def test_viewer_sighting_create():
    ViewerSightingCreate(viewer_login_name="yessir", viewerlist_fetch_id=uuid4())

    with pytest.raises((ValidationError, ValueError)):
        ViewerSightingCreate(viewer_login_name=123, viewerlist_fetch_id=uuid4())

    with pytest.raises((ValidationError, ValueError)):
        ViewerSightingCreate(viewer_login_name="weeee", viewerlist_fetch_id="no")

    with pytest.raises((ValidationError, ValueError)):
        ViewerSightingCreate(
            **{"viewer_login_name": "nope!!", "viewerlist_fetch_id": str(uuid4())}
        )

    # name of just numbers is technically legal
    ViewerSightingCreate(
        **{"viewer_login_name": "123", "viewerlist_fetch_id": str(uuid4())}
    )
