import logging
import os
from typing import Optional, Union

import yaml

logger = logging.getLogger("server")


class Config:
    PORT = 443

    LOGGING_CONFIG_FILE: str = os.getenv("LOG_CFG", "./logging_config.yaml")

    _sqlmodel_database_uri: Optional[str] = None

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
                cls.TWITCH_CLIENT_ID = secrets["TWITCH_CLIENT_ID"]
                cls.TWITCH_CLIENT_SECRET = secrets["TWITCH_CLIENT_SECRET"]

    @classmethod
    def _build_db_uri(cls) -> str:
        mysql_user_password: Optional[str] = None
        pw_file = os.getenv("MYSQL_USER_PASSWORD_FILE")
        if pw_file is None:
            raise EnvironmentError("MYSQL_USER_PASSWORD_FILE not in environment.")
        with open(pw_file, "r", encoding="utf8") as file:
            mysql_user_password = file.read().strip()
        if len(mysql_user_password) == 0:
            raise EnvironmentError("MYSQL_USER_PASSWORD_FILE is empty.")
        uri = f"mysql+aiomysql://user:{mysql_user_password}@db/lurkerbothunterdb"
        return uri

    @classmethod
    def get_db_uri(cls) -> str:
        if cls._sqlmodel_database_uri is None:
            environment = os.getenv("ENVIRONMENT", "prod")
            if environment in ["test", "dev"]:
                cls._sqlmodel_database_uri = "sqlite+aiosqlite://"
            else:
                cls._sqlmodel_database_uri = cls._build_db_uri()

        return cls._sqlmodel_database_uri
