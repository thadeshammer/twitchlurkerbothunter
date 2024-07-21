from typing import List

from pydantic import BaseModel


class User(BaseModel):
    id: str
    login: str
    display_name: str
    type: str
    broadcaster_type: str
    description: str
    profile_image_url: str
    offline_image_url: str
    view_count: int
    created_at: str


class GetUsersResponse(BaseModel):
    data: List[User]
