from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a base class for all declarative models to inherit from.
Base = declarative_base()
SessionLocal: Optional[sessionmaker] = None
engine: Optional[Engine] = None

def _init_db(database_uri: str):
    assert isinstance(database_uri, str)
    global engine, SessionLocal
    engine = create_engine(database_uri)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
