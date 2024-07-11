import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from server.db import get_db
from server.models import Secret, SecretCreate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/store-token")
async def store_token(request: Request):
    logger.info("/store-token accessed.")

    if not await request.json():
        logger.error("Missing JSON payload.")
        raise HTTPException(status_code=400, detail="Missing JSON payload")

    try:
        payload = await request.json()
        new_secret = SecretCreate(**payload)
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e.errors()}")

    logger.info(
        f"Tokens received. {new_secret.expires_in=}, {new_secret.token_type=}, {new_secret.scope=}"
    )

    async def insert_or_update_secret(new_secret: Secret):
        async with get_db() as db:
            try:
                db.add(new_secret)
                await db.commit()
                existing_secret = new_secret
            except IntegrityError:
                await db.rollback()
                result = await db.execute(
                    db.query(Secret).filter_by(enforce_one_row="enforce_one_row")
                )
                existing_secret = result.scalar()
                if existing_secret:
                    existing_secret.access_token = new_secret.access_token
                    existing_secret.refresh_token = new_secret.refresh_token
                    existing_secret.expires_in = new_secret.expires_in
                    existing_secret.token_type = new_secret.token_type
                    existing_secret.scope = new_secret.scope
                    await db.commit()

    await insert_or_update_secret(new_secret)

    return {"message": "ok"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@router.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}
