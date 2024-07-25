# server/core/twitch_api_delegate/twitch_api_delegate.py
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from pydantic import ValidationError

from server.models import (
    GetStreamResponse,
    StreamCategoryCreate,
    TwitchUserDataCreate,
    UserListResponse,
)

logger = logging.getLogger("__name__")


class TwitchAPIDelegateError(Exception):
    pass


class TwitchAPIDelegateTokenRefresh(TwitchAPIDelegateError):
    pass


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
    config: TwitchAPIConfig,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    headers = {
        "Client-ID": config.client_id,
        "Authorization": f"Bearer {config.access_token}",
    }
    if custom_headers:
        headers.update(custom_headers)

    url = base_url if base_url else config.base_url
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{url}/{endpoint}", params=params) as response:
            if response.status != 200:
                logger.error(f"Failed to make request: {response.status}")
                return {"error": response.status, "message": await response.text()}
            return await response.json()


def response_error_check(response: dict[str, Any]):
    """Checks a Twitch backend API response dict for error and surfaces the full error message if
    applicable.

    Args:
        response (dict[str, Any]): The full Twitch API response object.

    Raises:
        TwitchAPIDelegateError: If any errors came back with the response, this is raised.
    """
    if "error" in response:
        error_message = response.get("message", "Unknown error")
        logger.error(f"Twitch API error: {error_message}")
        raise TwitchAPIDelegateError(f"Twitch API error: {error_message}")


async def get_streams(
    get_streams_params: TwitchGetStreamsParams,
) -> tuple[list[GetStreamResponse], str]:
    params = {"first": get_streams_params.first or "20"}
    if get_streams_params.cursor is not None:
        # get next page of stream results
        params["after"] = get_streams_params.cursor
    else:
        # this is our first go
        if get_streams_params.game_id is not None:
            params["game_id"] = get_streams_params.game_id
        if get_streams_params.user_id is not None:
            params["user_id"] = get_streams_params.user_id
        if get_streams_params.user_login is not None:
            params["user_login"] = get_streams_params.user_login

    # Filter out None values from params
    # params = {k: v for k, v in params.items() if v is not None}
    logger.debug(f"{params=}")

    response = await make_request(
        get_streams_params.twitch_api_config, "streams", params
    )
    response_error_check(response=response)
    try:
        streams_data = response.get("data", [])
        pagination_cursor: str = response.get("pagination", {}).get("cursor", "")
        streams: list[GetStreamResponse] = [
            GetStreamResponse(**stream) for stream in streams_data
        ]
        return streams, pagination_cursor
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise


async def get_users(
    config: TwitchAPIConfig, login_names: list[str]
) -> list[TwitchUserDataCreate]:
    if len(login_names) > 100:
        raise TwitchAPIDelegateError("Limit 100 names for the 'Get Users' request.")

    params = {"login": login_names}
    response: dict[str, Any] = await make_request(config, "users", params)
    response_error_check(response=response)

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
            try:
                response_error_check(response=response)
                if response.status != 200:
                    logger.error(f"Failed to refresh token: {response.status}")
                    return {"error": response.status, "message": await response.text()}
                return await response.json()
            except TwitchAPIDelegateError as e:
                raise TwitchAPIDelegateTokenRefresh(
                    f"Failed to refresh tokens. {str(e)}"
                ) from e


async def check_token_validity(config: TwitchAPIConfig) -> bool:
    try:
        custom_headers = {
            "Authorization": f"OAuth {config.access_token}",
        }
        response = await make_request(
            config=config,
            endpoint="oauth2/validate",
            custom_headers=custom_headers,
            base_url="https://id.twitch.tv",
        )
        response_error_check(response=response)
        if "status" in response and response["status"] != 200:
            logger.error(f"Token validation failed: {response['message']}")
            return False
        return True
    except TwitchAPIDelegateError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Exception occurred during token validation: {str(e)}")
        raise


async def get_categories(
    config: TwitchAPIConfig,
    category_ids: Optional[list[str]] = None,
    category_names: Optional[list[str]] = None,
) -> list[StreamCategoryCreate]:

    id_count = len(category_ids) if category_ids else 0
    name_count = len(category_names) if category_names else 0
    if id_count + name_count > 100:
        raise TwitchAPIDelegateError("Limit 100 ids+names for 'Get Category' request.")

    params = {}
    if category_ids:
        params["id"] = category_ids
    if category_names:
        params["name"] = category_names

    logger.debug(f"{params=}")
    response = await make_request(config, "games", params)
    response_error_check(response=response)

    try:
        categories_data = response.get("data", [])
        logger.debug(f"{categories_data=}")
        categories = [StreamCategoryCreate(**category) for category in categories_data]
        logger.debug(f"{categories=}")
        return categories
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise


async def get_app_access_token(config: TwitchAPIConfig) -> Dict[str, Any]:
    """Fetch an App Access token, intended for public API data. 800 requests per minute but limited
    access (can't fetch follower info for instance)."""
    params = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "grant_type": "client_credentials",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(config.oauth_token_url, params=params) as response:
            if response.status != 200:
                logger.error(f"Failed to get app access token: {response.status}")
                raise TwitchAPIDelegateError(
                    f"Failed to get app access token: {response.status}"
                )
            data = await response.json()
            return {
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type"),
            }


async def get_channel_user_list(
    config: TwitchAPIConfig, channel_name: str
) -> UserListResponse:
    # The ill-fated undocumented endpoint to get user list from a channel
    endpoint = f"group/user/{channel_name}/chatters"
    tmi_base_url = "https://tmi.twitch.tv"
    response = await make_request(config, endpoint, base_url=tmi_base_url)
    response_error_check(response=response)
    try:
        user_list_response = UserListResponse(**response)
        return user_list_response
    except ValidationError as e:
        logger.error(f"Error parsing response: {e}")
        raise
