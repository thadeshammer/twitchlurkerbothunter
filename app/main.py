"""
Main application entry point.

TODO write up summary here

Run the application:
    - Build and start the application with Docker:
      docker-compose build && docker-compose up
    - You can use the provided rebuild.sh if that's helpful in iterative development. (It was
    invaluable for me.) NOTE that running docker-compose down will result in the destruction of
    all data on the Postgres instance unless you mount a volume for that.
    - TODO can we get Swagger back in here?

Dependencies:
    - TODO fill this out, we're using Flask now
    - SQLAlchemy: ORM for database interactions.

Usage:
    - Import this module and run the FastAPI application.
"""

from typing import Any, Dict, List
import uuid

from sqlalchemy.orm import Session

from server.db import get_db
from server.db.models import TestData, TestModel

