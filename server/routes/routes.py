import logging
from datetime import datetime, timezone
from typing import Optional

import pytz
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from server.config import Config
from server.core.twitch_api_delegate import (
    TwitchAPIConfig,
    TwitchGetStreamsParams,
    get_streams,
    get_user,
)
from server.core.twitch_secrets_manager import TwitchSecretsManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/store-token")
async def store_token(request: Request):
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


@router.get("/force-tokens-refresh")
async def force_tokens_refresh():
    logger.debug("In /force-tokens-refresh")
    try:
        secrets_manager = TwitchSecretsManager()
        await secrets_manager.force_tokens_refresh()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tokens force-refresh failed: Internal Server Error",
        ) from e

    return {"message": "ok"}


@router.get("/healthcheck")
async def healthcheck():
    current_time = datetime.now(timezone.utc)

    try:
        local_timezone = pytz.timezone(Config.LOCAL_TIMEZONE)
        server_start_local = Config.server_start_time.astimezone(local_timezone)
        current_time_local = current_time.astimezone(local_timezone)
    except pytz.UnknownTimeZoneError:
        logger.error(
            f"Check config: {Config.LOCAL_TIMEZONE} is unknown. Defaulting to {Config.DEFAULT_TIMEZONE}"
        )
        local_timezone = pytz.timezone(Config.DEFAULT_TIMEZONE)
        server_start_local = "Error: check config. Use IANA db timezone code."
        current_time_local = "Error: check config. Use IANA db timezone code."

    uptime = current_time - Config.server_start_time
    return {
        "status": "ok",
        "server_start_time": f"{Config.server_start_time.isoformat()} ({server_start_local})",
        "current_time": f"{current_time.isoformat()} ({current_time_local})",
        "uptime": str(uptime),
    }


@router.get("/")
async def read_root():
    return {"message": "ohai!"}


@router.get("/streams")
async def get_streams_endpoint(
    game_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_login: Optional[str] = None,
    first: Optional[str] = None,  # streams per page
    cursor: Optional[str] = None,
):
    try:
        secrets_manager = TwitchSecretsManager()
        config = TwitchAPIConfig(**(await secrets_manager.get_credentials()))
        params = TwitchGetStreamsParams(
            twitch_api_config=config,
            game_id=game_id,
            user_id=user_id,
            user_login=user_login,
            first=first,
            cursor=cursor,
        )
        streams_response, pagination_cursor = await get_streams(params)

        # Return the first page of the response
        return {
            "streams": [s.model_dump() for s in streams_response],
            "cursor": pagination_cursor,
        }
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
        if user_response is not None:
            return user_response.model_dump()

        return {"message": "User not found."}
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
