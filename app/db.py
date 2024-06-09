# app/db.py
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.exceptions import DatabaseConnectionError

from .db_base import SessionLocal

MAX_RETRIES = 5
RETRY_INTERVAL = 5


def _get_session() -> Session:
    retries = 0
    while retries < MAX_RETRIES:
        try:
            db = SessionLocal()
        except OperationalError as e:
            retries += 1
            time.sleep(RETRY_INTERVAL)
            if retries >= MAX_RETRIES:
                raise DatabaseConnectionError(
                    "Failed to connect to the database after multiple retries."
                ) from e
    return db


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = _get_session()
    try:
        yield db
    finally:
        db.close()
