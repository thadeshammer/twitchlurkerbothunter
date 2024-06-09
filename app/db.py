# app/db.py
import time
from sqlalchemy.orm import Session
from .db_base import Base, SessionLocal

MAX_RETRIES = 5
RETRY_INTERVAL = 5

def _get_session() -> Session:
    retries = 0
    while retries < MAX_RETRIES:
        try:
            db = SessionLocal()
            return db
        except Exception as e:
            retries += 1
            time.sleep(RETRY_INTERVAL)
            if retries >= MAX_RETRIES:
                raise e

def get_db() -> Session:
    db = _get_session()
    try:
        yield db
    finally:
        db.close()
