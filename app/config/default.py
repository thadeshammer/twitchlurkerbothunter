import os
from enum import StrEnum
from typing import Optional, Union

import yaml


class ConfigKey(StrEnum):
    # Use these to access current_app.config[KEY]
    LOGGING_CONFIG_FILE = "LOGGING_CONFIG_FILE"

    SQLALCHEMY_DATABASE_URI = "SQLALCHEMY_DATABASE_URI"
    SQLALCHEMY_TRACK_MODIFICATIONS = "SQLALCHEMY_TRACK_MODIFICATIONS"
    SQLALCHEMY_CONNECT_MAX_RETRIES = "SQLALCHEMY_CONNECT_MAX_RETRIES"
    SQLALCHEMY_CONNECT_RETRY_INTERVAL = "SQLALCHEMY_CONNECT_RETRY_INTERVAL"

    TWITCH_ACCESS_TOKEN = "TWITCH_ACCESS_TOKEN"
    TWITCH_CLIENT_ID = "TWITCH_CLIENT_ID"
    TWITCH_CLIENT_SECRET = "TWITCH_CLIENT_SECRET"


class Config:
    LOGGING_CONFIG_FILE: str = os.getenv("LOG_CFG", "./logging_config.yaml")

    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://user:password@db/mydatabase"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_CONNECT_MAX_RETRIES: int = 5
    SQLALCHEMY_CONNECT_RETRY_INTERVAL: int = 5

    # The access token is supplied by the twitch_oauth.sh servlet via the store_token endpoint.
    # See app.routes
    TWITCH_ACCESS_TOKEN: Optional[str] = None
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
