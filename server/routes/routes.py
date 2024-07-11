import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

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
        raise HTTPException(
            status_code=400, detail=f"Validation error: {e.errors()}"
        ) from e

    logger.info(
        f"Tokens received. {new_secret.expires_in=}, {new_secret.token_type=}, {new_secret.scope=}"
    )

    async def insert_or_update_secret(new_secret: SecretCreate):
        secret = Secret(**new_secret.model_dump())
        async with get_db() as db:
            try:
                logger.info("Writing secrets to DB, new row.")
                db.add(secret)
                await db.commit()
                existing_secret = secret
            except IntegrityError:
                logger.info("Existing secrets in DB, updating.")
                await db.rollback()
                statement = select(Secret).where(
                    Secret.enforce_one_row == "enforce_one_row"
                )
                result = await db.execute(statement)
                existing_secret = result.scalar()
                if existing_secret:
                    existing_secret.access_token = secret.access_token
                    existing_secret.refresh_token = secret.refresh_token
                    existing_secret.expires_in = secret.expires_in
                    existing_secret.token_type = secret.token_type
                    existing_secret.scope = secret.scope
                    await db.commit()

    try:
        await insert_or_update_secret(new_secret)
    except Exception as e:
        logger.error(f"Failed to insert or update secret: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e

    logger.info("Done updating secrets; route complete.")

    return {"message": "ok"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@router.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}
