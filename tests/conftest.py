import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker  # type: ignore

from app.db import Base


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):  # pylint: disable=redefined-outer-name
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine, tables):  # pylint: disable=redefined-outer-name
    """Returns an SQLAlchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)  # pylint: disable=invalid-name
    session = Session()  # pylint: disable=redefined-outer-name

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    # clear_mappers()
