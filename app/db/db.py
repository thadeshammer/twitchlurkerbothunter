# app/db.py
import time
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import DatabaseConnectionError

from .db_base import SessionLocal

# Module-level variables to store configuration
_max_retries: int = 0
_retry_interval: int = 0


def init_db(database_uri: str, max_retries: int, retry_interval: int) -> None:
    """
    Initializes the database engine and session factory,
    and sets retry configuration values.
    """
    assert isinstance(database_uri, str)
    assert isinstance(max_retries, int)
    assert isinstance(retry_interval, int)

    from .db_base import _init_db as base_init_db
    global _max_retries, _retry_interval
    base_init_db(database_uri)
    _max_retries = max_retries
    _retry_interval = retry_interval


def _get_session() -> Session:
    """
    Attempts to establish a SQLAlchemy database session with retry logic.

    Retries connecting to the db a specified number of times
    with a delay between attempts, based on configuration settings.

    Returns:
        Session: A SQLAlchemy Session object.

    Raises:
        DatabaseConnectionError: If the connection to the database
        cannot be established after the maximum number of retries.
    """

    retries: int = 0

    db: Optional[Session] = None
    while retries < _max_retries and db is None:
        try:
            assert isinstance(SessionLocal, sessionmaker)
            db = SessionLocal()
        except OperationalError as e:  # retry logic
            retries += 1
            time.sleep(_retry_interval)
            if retries >= _max_retries:
                raise DatabaseConnectionError(
                    f"Failed to connect to the database after {retries} retries."
                ) from e

    assert db is not None  # It it were, we'd have raised an exception already.
    return db


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provides a SQLAlchemy database session context manager.
    Ensures that the session is properly closed after use regardless of errors.

    Yields:
        Generator[Session, None, None]: _description_
    """
    db: Session = _get_session()
    try:
        yield db
    finally:
        db.close()
