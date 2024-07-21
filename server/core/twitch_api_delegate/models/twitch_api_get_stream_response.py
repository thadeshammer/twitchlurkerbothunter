# server/core/twitch_api_delegate/models/twitch_api_stream_response.py
from typing import List, Optional

from pydantic import BaseModel


class Pagination(BaseModel):
    cursor: Optional[str] = None


class Stream(BaseModel):
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    type: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    tag_ids: Optional[List[str]] = None
    is_mature: bool


class GetStreamsResponse(BaseModel):
    data: List[Stream]
    pagination: Pagination
