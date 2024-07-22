# server/core/twitch_api_delegate/twitch_api_delegate.py
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from pydantic import ValidationError

from server.models import GetStreamResponse, TwitchUserDataCreate

logger = logging.getLogger("__name__")


@dataclass
class TwitchAPIConfig:
    access_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    base_url: str = "https://api.twitch.tv/helix"
    oauth_token_url: str = "https://id.twitch.tv/oauth2/token"


@dataclass
class TwitchGetStreamsParams:
    twitch_api_config: TwitchAPIConfig
    game_id: Optional[str] = None
    user_id: Optional[str] = None
    user_login: Optional[str] = None
    first: str = "20"
    cursor: Optional[str] = None


async def make_request(
    config: TwitchAPIConfig, endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    headers = {
        "Client-ID": config.client_id,
        "Authorization": f"Bearer {config.access_token}",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            f"{config.base_url}/{endpoint}", params=params
        ) as response:
            if response.status != 200:
                logger.error(f"Failed to make request: {response.status}")
                return {"error": response.status, "message": await response.text()}
            return await response.json()


async def get_streams(
    get_streams_params: TwitchGetStreamsParams,
) -> tuple[list[GetStreamResponse], str]:
    params = {"first": get_streams_params.first}
    if get_streams_params.cursor is not None:
        # get next page of stream results
        params["after"] = get_streams_params.cursor
    else:
        # this is our first go
        if get_streams_params.game_id:
            params["game_id"] = get_streams_params.game_id
        if get_streams_params.user_id:
            params["user_id"] = get_streams_params.user_id
        if get_streams_params.user_login:
            params["user_login"] = get_streams_params.user_login

    response = await make_request(
        get_streams_params.twitch_api_config, "streams", params
    )
    try:
        streams_data = response.get("data", [])
        pagination_cursor = response.get("pagination", {}).get("cursor", "")
        streams = [GetStreamResponse(**stream) for stream in streams_data]
        return streams, pagination_cursor
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise


async def get_users(
    config: TwitchAPIConfig, login_names: list[str]
) -> list[TwitchUserDataCreate]:
    params = {"login": login_names}

    response = await make_request(config, "users", params)
    try:
        users_data = response.get("data", [])
        return [TwitchUserDataCreate(**user) for user in users_data]
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise


async def get_user(
    config: TwitchAPIConfig, login_name: str
) -> Optional[TwitchUserDataCreate]:
    users = await get_users(config, [login_name])
    return users[0] if users else None


async def revitalize_tokens(
    config: TwitchAPIConfig, refresh_token: str
) -> Dict[str, Any]:
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": config.client_id,
        "client_secret": config.client_secret,
    }
    logger.debug("Calling refresh endpoint.")
    async with aiohttp.ClientSession() as session:
        async with session.post(config.oauth_token_url, params=params) as response:
            if response.status != 200:
                logger.error(f"Failed to refresh token: {response.status}")
                return {"error": response.status, "message": await response.text()}
            return await response.json()


# Example usage
# async def main():
#     config = TwitchAPIConfig(..stuff it needs..)

#     streams = await get_streams(config, game_id="21779")  # Example game_id
#     print(streams)
