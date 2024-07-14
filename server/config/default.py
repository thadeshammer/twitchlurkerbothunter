import logging
import os
from enum import StrEnum
from typing import Optional, Union

import yaml


logger = logging.getLogger("server")


def _build_db_uri() -> str:
    mysql_user_password: Optional[str] = None
    pw_file = os.getenv("MYSQL_USER_PASSWORD_FILE")
    if pw_file is None:
        raise EnvironmentError("MYSQL_USER_PASSWORD_FILE not in environment.")
    with open(pw_file, "r") as file:
        mysql_user_password = file.read().strip()
    if len(mysql_user_password) == 0:
        raise EnvironmentError("MYSQL_USER_PASSWORD_FILE is empty.")
    uri = f"mysql+aiomysql://user:{mysql_user_password}@db/lurkerbothunterdb"
    return uri


class ConfigKey(StrEnum):
    # Use these to access current_app.config[KEY]
    PORT = "PORT"

    LOGGING_CONFIG_FILE = "LOGGING_CONFIG_FILE"

    SQLALCHEMY_DATABASE_URI = "SQLALCHEMY_DATABASE_URI"

    TWITCH_ACCESS_TOKEN = "TWITCH_ACCESS_TOKEN"
    TWITCH_REFRESH_TOKEN = "TWITCH_REFRESH_TOKEN"
    TWITCH_CLIENT_ID = "TWITCH_CLIENT_ID"
    TWITCH_CLIENT_SECRET = "TWITCH_CLIENT_SECRET"


class Config:
    PORT = 443

    LOGGING_CONFIG_FILE: str = os.getenv("LOG_CFG", "./logging_config.yaml")

    SQLMODEL_DATABASE_URI: str = _build_db_uri()

    # The access and refresh tokens are supplied by the twitch_oauth.sh servlet via the store_token
    # endpoint. See server.routes
    TWITCH_ACCESS_TOKEN: Optional[str] = None
    TWITCH_REFRESH_TOKEN: Optional[str] = None

    # Client ID and Secret are loaded in from secrets/ on disk.
    TWITCH_CLIENT_ID: Optional[str] = None
    TWITCH_CLIENT_SECRET: Optional[str] = None

    @classmethod
    def load_secrets(cls) -> None:
        secrets_path: str = os.getenv("SECRETS_DIR", "./secrets/tokens.yaml")

        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="UTF8") as file:
                secrets: Union[dict, list, None] = yaml.safe_load(file)
                assert isinstance(secrets, dict)
                cls.TWITCH_CLIENT_ID = secrets[ConfigKey.TWITCH_CLIENT_ID]
                cls.TWITCH_CLIENT_SECRET = secrets[ConfigKey.TWITCH_CLIENT_SECRET]
