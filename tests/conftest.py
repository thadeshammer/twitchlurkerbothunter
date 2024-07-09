import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.scanning_session import ScanningSession
from app.models.stream_categories import StreamCategory
from app.models.stream_viewerlist_fetch import StreamViewerListFetch
from app.models.suspected_bot import SuspectedBot
from app.models.twitch_user_data import TwitchUserData
from app.models.viewer_sighting import ViewerSighting


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
