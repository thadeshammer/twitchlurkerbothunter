"""
Main application entry point.

This module sets up and runs the FastAPI application, including route definitions and
rate limiting with SlowAPI.

Run the application:
    - Build and start the application with Docker:
      docker-compose build && docker-compose up
    - You can use the provided rebuild.sh if that's helpful in iterative development. (It was
    invaluable for me.) NOTE that running docker-compose down will result in the destruction of
    all data on the Postgres instance unless you mount a volume for that.
    - Access the API documentation at:
      http://localhost/docs

Dependencies:
    - FastAPI: Web framework for building APIs with Python.
    - SlowAPI: Rate limiting for FastAPI.
    - SQLAlchemy: ORM for database interactions.

Usage:
    - Import this module and run the FastAPI application.
"""

from typing import Any, Dict, List
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from server.db import get_db
from server.db.models import TestData, TestModel

# Initialize rate limiter with SlowAPI using the client's remote address as the key
# Reference: https://stackoverflow.com/questions/65491184/ratelimit-in-fastapi
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def read_root():
    """Root endpoint.

    Returns:
        dict: A dict containing the message "Ready."
    """
    return {"message": "Ready."}


@app.post("/addname")
async def addname_endpoint(
    name: str, db_session: Session = Depends(get_db)) -> Dict[str, Any]:
    """ENDPOINT: add a name(str) to the database table, test_table.

    Args:
        name (str): A name? What's in a name.
        db_session (Session, optional): DB Session dependency, received via inject.

    Raises:
        HTTPException: If an error occurs due to db interaction.

    Returns:
        Dict[str, Any]: dict containing a success message, UID, and the full test data.
    """
    try:
        # unpack the payload, create and add UID
        uid = str(uuid.uuid4())
        test_data = TestData(uid=uid, name=name)

        db_data = TestModel(**test_data.dict())

        db_session.add(db_data)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        db_session.close()

    return {"message": "Success.", "uid": uid, "data": test_data}


@app.get("/getnames", response_model=List[TestData])
@limiter.limit("10/minute")  # slowapi limiter example
async def getnames_endpoint(  # NOTE SlowAPI requires the request param, even if unused otherwise.
    request: Request,
    db_session: Session = Depends(get_db)) -> List[Dict[str, str]]:
    """Endpoint to retrieve all test entries from the database.

    Args:
        request (Request): The request object (required by SlowAPI for rate limiting).
        db_session (Session): The database session dependency.

    Raises:
        HTTPException: If no data is found in the database.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the UID and name of each test entry.
    """
    all_data = db_session.query(TestModel).all()

    if not all_data:
        raise HTTPException(status_code=404, detail="No data.")

    return [{"uid": d.uid, "name": d.name} for d in all_data]
