import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from server.core.twitch_api_delegate import TwitchAPIConfig, get_streams, get_user
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


@router.get("/streams")
async def get_streams_endpoint(
    game_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_login: Optional[str] = None,
):
    try:
        secrets_manager = TwitchSecretsManager()
        config = TwitchAPIConfig(**(await secrets_manager.get_credentials()))
        streams_response = await get_streams(config, game_id, user_id, user_login)

        # Return the first page of the response
        return streams_response.model_dump_json()
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(
            status_code=400, detail=f"Validation error: {e.errors()}"
        ) from e
    except Exception as e:
        logger.error(f"Error fetching streams: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch streams: Internal Server Error",
        ) from e


@router.get("/user/{username}")
async def get_user_endpoint(username: str):
    try:
        # Retrieve credentials from SecretsManager
        secrets_manager = TwitchSecretsManager()
        config = TwitchAPIConfig(**(await secrets_manager.get_credentials()))
        user_response = await get_user(config, username)

        # Return the user information
        return user_response.model_dump_json()
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(
            status_code=400, detail=f"Validation error: {e.errors()}"
        ) from e
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}",
        ) from e
