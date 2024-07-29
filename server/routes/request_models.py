# /server/routes/request_models.py
from pydantic import BaseModel


class StringList(BaseModel):
    items: list[str]
