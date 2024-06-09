"""
SQLAlchemy interface module main file

Encapsulates setup  and management of the db connection for the application. It provivdes a
generator function `get_db` for obtaining database sessions, ensuring proper initialization and
resource cleanup.

SQLAlchemy interface module main file.

This module encapsulates the setup and management of the database connection
for the application. It provides a generator function `get_db` for obtaining
database sessions, ensuring proper initialization and cleanup of resources.

Usage:
    - Import `get_db` in your FastAPI routes or other parts of your application
      where you need to interact with the database.
    - The models must be imported so they're registered with SQLAlchemy's Base
    metadata; home them in .models and include them in models/__init.py__.
    - DO NOT USE `_get_engine` or `_get_session` directly; they are intended for
      internal use only to manage the database engine and session creation.

Functions:
    - _get_engine: Initializes and returns the SQLAlchemy engine.
    - _get_session: Creates and returns a new SQLAlchemy session.
    - get_db: Dependency generator that yields a SQLAlchemy session.

Constants:
    - DATABASE_URL: The URL for connecting to the PostgreSQL database.
    - MAX_RETRIES: The maximum number of retries for connecting to the database.
    - RETRY_INTERVAL: The interval (in seconds) between connection retries.

Dependencies:
    - SQLAlchemy: Used for database ORM and connection management.
    - psycopg2-binary: PostgreSQL adapter for Python.

Note:
    - Ensure that the `DATABASE_URL`, `MAX_RETRIES`, and `RETRY_INTERVAL`
      constants are configured according to your environment and requirements.
    - The models must be imported for their side effects to register with
      SQLAlchemy's Base metadata.
"""
import time
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from .models import TestModel  # pylint: disable=unused-import

# TODO home these constants in configuration
DATABASE_URL = URL(drivername="postgresql",
                   username="myuser",
                   password="mypassword",
                   host="postgres",
                   database="default_database",
                   port=5432)

MAX_RETRIES = 5
RETRY_INTERVAL = 5

_engine: Optional[Engine] = None
_session_local: Optional[sessionmaker] = None


def _get_engine() -> Optional[Engine]:
    """Returns the SQLAlchemy engine singleton instance; will attempt to create the engine if it
    hasn't been done yet.

    If the singleton _engine hasn't yet been populated, this method will call create_engine up to
    MAX_RETRIES with a timeout of RETRY_INTERVAL.

    Raises:
        e: OperationalError re-raised if we fail to connect.

    Returns:
        Optional[Engine]: The SQLAlchemy engine for the application.
    """
    global _engine
    if _engine is None:
        retries = 0

        while retries < MAX_RETRIES and _engine is None:
            try:
                _engine = create_engine(DATABASE_URL)
                Base.metadata.create_all(_engine)
                print("DB connect success.")
            except OperationalError as e:
                print(
                    f"Error connecting to the database on try {retries}: {e}")
                retries += 1
                if retries < MAX_RETRIES:
                    print(f"Retrying in {RETRY_INTERVAL} seconds...")
                    time.sleep(RETRY_INTERVAL)
                else:
                    print("Max retries exceeded. Exiting.")
                    raise e

    return _engine


def _get_session() -> Session:
    """Returns the application's SQLAlchemy session, creating it if necessary.

    Returns:
        Session: SQLAlchemy session instance.
    """
    global _session_local
    if _session_local is None:
        e = _get_engine()
        _session_local = sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=e)
    return _session_local()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator that yields a SQLAlchemy Session.

    Yields:
        Generator[Session, None, None]: SQLAlchemy session instance.
    """
    db: Session = _get_session()
    try:
        yield db
    finally:
        # release connection back to pool
        db.close()


# Ensures that the engine and tables are initialized at module load time.
if _engine is None:
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)
