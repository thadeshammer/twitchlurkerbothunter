# app/db.py
import time
from contextlib import contextmanager
from typing import Generator, Optional

from flask import current_app
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import ConfigKey
from app.exceptions import DatabaseConnectionError

from .base import SessionLocal


def _get_session() -> Session:
    retries = 0
    max_retries = current_app.config[ConfigKey.SQLALCHEMY_CONNECT_MAX_RETRIES]
    retry_interval = current_app.config[ConfigKey.SQLALCHEMY_CONNECT_RETRY_INTERVAL]

    db: Optional[Session] = None
    while retries < max_retries and db is None:
        try:

            db = SessionLocal()

        except OperationalError as e:
            retries += 1
            time.sleep(retry_interval)
            if retries >= max_retries:
                raise DatabaseConnectionError(
                    "Failed to connect to the database after multiple retries."
                ) from e

    assert db is not None  # It it were, we'd have raised an exception already.
    return db


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = _get_session()
    try:
        yield db
    finally:
        db.close()
