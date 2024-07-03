import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):  # pylint: disable=redefined-outer-name
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
@pytest.fixture(scope="function")
def session(engine, tables):
    with Session(engine) as session:  # type: ignore
        yield session
