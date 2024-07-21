import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class Config:
    _initialized = False

    server_start_time = datetime.now(timezone.utc)

    PORT = 443
    ENVIRONMENT = os.getenv("ENVIRONMENT", "dev").lower()
    LOGGING_CONFIG_FILE: str = os.getenv("LOG_CFG", "./logging_config.yaml")

    DEFAULT_TIMEZONE = "UTC"
    LOCAL_TIMEZONE = os.getenv("LOCAL_TIMEZONE", DEFAULT_TIMEZONE)

    _sqlmodel_database_uri: Optional[str] = None
    _db_name: Optional[str] = None

    # defaults are typical test-db (MySQL) instance
    MYSQL_USER_PASSWORD_FILE: Optional[str] = None
    TESTDB_PASSWORD_FILE_FALLBACK = "./secrets/.testdb_user_password.txt"
    DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "mysql+aiomysql://")
    DBNAME = os.getenv("DATABASE_NAME", "lurkerbothunter-testdb")
    DBSERVICE_NAME = os.getenv(
        "DB_SERVICE_NAME", "localhost"
    )  # "test-db" docker service name
    DBPORT = os.getenv("DB_PORT", "3307")

    # defaults are typical test-redis instance
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6380")
    REDIS_DB_INDEX = os.getenv("REDIS_DB", "0")

    # The access and refresh tokens are supplied by the twitch_oauth.sh servlet via the store_token
    # endpoint. See server.routes
    TWITCH_ACCESS_TOKEN: Optional[str] = None
    TWITCH_REFRESH_TOKEN: Optional[str] = None

    # Client ID and Secret are loaded in from secrets/ on disk.
    TWITCH_CLIENT_ID: Optional[str] = None
    TWITCH_CLIENT_SECRET: Optional[str] = None

    # Rate limits
    TWITCH_CHANNEL_JOIN_LIMIT_COUNT = int(
        os.getenv("TWITCH_CHANNEL_JOIN_LIMIT_COUNT", "20")
    )
    TWITCH_CHANNEL_JOIN_LIMIT_PER_SECONDS = int(
        os.getenv("TWITCH_CHANNEL_JOIN_LIMIT_PER_SECONDS", "10")
    )

    @classmethod
    def initialize(cls) -> None:
        twitch_oauth_secrets_path: str = os.getenv(
            "SECRETS_DIR", "./secrets/tokens.yaml"
        )

        if os.path.exists(twitch_oauth_secrets_path):
            with open(twitch_oauth_secrets_path, "r", encoding="UTF8") as file:
                secrets: Union[dict, list, None] = yaml.safe_load(file)
                if not isinstance(secrets, dict):
                    raise TypeError("secrets load failed.")
                cls.TWITCH_CLIENT_ID = secrets["TWITCH_CLIENT_ID"]
                cls.TWITCH_CLIENT_SECRET = secrets["TWITCH_CLIENT_SECRET"]

        if cls.ENVIRONMENT == "prod":
            cls.MYSQL_USER_PASSWORD_FILE = os.getenv("MYSQL_USER_PASSWORD_FILE")
            cls._db_name = os.getenv("DATABASE_NAME")
        elif cls.ENVIRONMENT in {"test", "dev"}:
            cls.MYSQL_USER_PASSWORD_FILE = os.getenv(
                "TESTDB_USER_PASSWORD", cls.TESTDB_PASSWORD_FILE_FALLBACK
            )
            cls._db_name = os.getenv("TEST_DB_NAME")
        else:
            raise ValueError("Invalid ENVIRONMENT set.")

        cls._initialized = True

    @classmethod
    def _build_db_uri(cls) -> str:
        if not cls._initialized:
            cls.initialize()

        mysql_user_password: Optional[str] = None
        pw_file = cls.MYSQL_USER_PASSWORD_FILE

        if pw_file is None:
            raise EnvironmentError(f"DB password file not set: {pw_file}")
        try:
            with open(pw_file, "r", encoding="utf8") as file:
                mysql_user_password = file.read().strip()
        except FileNotFoundError as e:
            raise EnvironmentError(f"DB password file missing: {pw_file}") from e
        if len(mysql_user_password) == 0:
            raise EnvironmentError(f"DB password file is empty: {pw_file}")

        # uri = f"mysql+aiomysql://user:{mysql_user_password}@db/lurkerbothunterdb"
        # uri = f"mysql+aiomysql://user:{password}@test-db:3307/lurkerbothunter-testdb"
        prefix = cls.DATABASE_PREFIX
        credentials = f"user:{mysql_user_password}"
        if cls.DBPORT is not None:
            service_and_port = f"{cls.DBSERVICE_NAME}:{cls.DBPORT}"
        else:
            service_and_port = f"{cls.DBSERVICE_NAME}:3306"
        uri = f"{prefix}{credentials}@{service_and_port}/{cls.DBNAME}"
        return uri

    @classmethod
    def get_db_uri(cls) -> str:
        if cls._sqlmodel_database_uri is None:
            cls._sqlmodel_database_uri = cls._build_db_uri()

        return cls._sqlmodel_database_uri

    @classmethod
    def get_redis_args(cls) -> dict[str, Any]:
        return {
            "host": Config.REDIS_HOST,
            "port": Config.REDIS_PORT,
            "db": Config.REDIS_DB_INDEX,
            "decode_responses": True,
        }
