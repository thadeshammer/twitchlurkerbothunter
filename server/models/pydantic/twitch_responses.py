"""
    TwitchResponses

    BaseModels for parsing and validating Twitch API responses we don't want to persist.
"""

from pydantic import BaseModel


class Chatters(BaseModel):
    broadcaster: list[str]
    vips: list[str]
    moderators: list[str]
    staff: list[str]
    admins: list[str]
    global_mods: list[str]
    viewers: list[str]


class UserListResponse(BaseModel):
    chatter_count: int
    chatters: Chatters
