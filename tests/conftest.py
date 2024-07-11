import logging

import pytest
from sqlmodel import Session, SQLModel, create_engine

from server.models.scanning_session import ScanningSession
from server.models.stream_categories import StreamCategory
from server.models.stream_viewerlist_fetch import StreamViewerListFetch
from server.models.suspected_bot import SuspectedBot
from server.models.twitch_user_data import TwitchUserData
from server.models.viewer_sighting import ViewerSighting


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):  # pylint: disable=redefined-outer-name
    print(f"Tables in metadata before creation: {SQLModel.metadata.tables.keys()}")
    SQLModel.metadata.create_all(engine)
    print(f"Tables in metadata after creation: {SQLModel.metadata.tables.keys()}")
    yield
    SQLModel.metadata.drop_all(engine)


# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
@pytest.fixture(scope="function")
def session(engine, tables):
    with Session(engine) as session:  # type: ignore
        yield session


@pytest.fixture(autouse=True)
def disable_logging():
    """Automatically disable logging for all unit tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
