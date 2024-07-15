import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from server.core.twitch_secrets_manager import TwitchSecretsManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/store-token")
async def store_token(request: Request):
    logger.debug("/store-token accessed.")

    if not await request.json():
        raise HTTPException(status_code=400, detail="Missing JSON payload")

    try:
        payload = await request.json()
        secrets_manager = TwitchSecretsManager()
        await secrets_manager.process_token_update_from_servlet(payload)
    except ValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Validation error: {e.errors()}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SecretUpdate failed: Internal Server Error",
        ) from e

    return {"message": "ok"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@router.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}
