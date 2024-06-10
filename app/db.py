# app/db.py
import time
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.exceptions import DatabaseConnectionError

from .db_base import SessionLocal

MAX_RETRIES = 5
RETRY_INTERVAL = 5


def _get_session() -> Session:
    retries = 0

    db: Optional[Session] = None
    while retries < MAX_RETRIES and db is None:
        try:
            print("calling SessionLocal", flush=True)
            db = SessionLocal()
            print("returned from SessionLocal call", flush=True)
        except OperationalError as e:
            retries += 1
            time.sleep(RETRY_INTERVAL)
            if retries >= MAX_RETRIES:
                raise DatabaseConnectionError(
                    "Failed to connect to the database after multiple retries."
                ) from e

    assert db is not None  # It it were, we'd have raised an exception already.
    return db


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = _get_session()
    try:
        print("yielding dat db hopefully", flush=True)
        yield db
    finally:
        print("closing db session", flush=True)
        db.close()
