# server/core/twitch_api_delegate/twitch_api_delegate.py
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from pydantic import ValidationError

from server.models import TwitchUserDataCreate

from .models import GetStreamsResponse

logger = logging.getLogger("__name__")


@dataclass
class TwitchAPIConfig:
    access_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    base_url: str = "https://api.twitch.tv/helix"


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
    config: TwitchAPIConfig,
    game_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_login: Optional[str] = None,
    first: str = "20",
) -> GetStreamsResponse:
    params = {"first": first}
    if game_id:
        params["game_id"] = game_id
    if user_id:
        params["user_id"] = user_id
    if user_login:
        params["user_login"] = user_login

    response = await make_request(config, "streams", params)
    try:
        return GetStreamsResponse(**response)
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise


async def get_more_streams(
    config: TwitchAPIConfig,
    cursor: str,
    game_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_login: Optional[str] = None,
    first: int = 20,
) -> GetStreamsResponse:
    params = {"first": first, "after": cursor}
    if game_id:
        params["game_id"] = game_id
    if user_id:
        params["user_id"] = user_id
    if user_login:
        params["user_login"] = user_login

    response = await make_request(config, "streams", params)
    try:
        return GetStreamsResponse(**response)
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


# Example usage
# async def main():
#     config = TwitchAPIConfig(..stuff it needs..)

#     streams = await get_streams(config, game_id="21779")  # Example game_id
#     print(streams)
