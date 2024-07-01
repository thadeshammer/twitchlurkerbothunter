# app/models/_validator_regexes.py
# A centralized spot for regexes used in data validation for Twitch API responses.
import re
from typing import Any

APP_UUID4_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
IN_APP_NOTES_REGEX = r"^[a-zA-Z0-9\s.,;!?-_@#%&()+=:/'\"]*$"
LANGUAGE_CODE_REGEX = r"^[a-z]{2}$"
TWITCH_LOGIN_NAME_REGEX = r"^[a-z0-9_]{1,25}$"
TWITCH_TOKEN_REGEX = r"^[a-zA-Z0-9]+$"


def matches_regex(value: Any, pattern: str) -> str:
    """Check if the given value matches the provided regex pattern."""
    if not isinstance(value, str) or not bool(re.match(pattern, value)):
        raise ValueError
    return value
