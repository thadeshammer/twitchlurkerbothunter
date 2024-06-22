# app/models/_validator_regexes.py

APP_UUID4_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
IN_APP_NOTES_REGEX = r"^[a-zA-Z0-9\s.,;!?-_@#%&()+=:/'\"]*$"
LANGUAGE_CODE_REGEX = r"^[a-z]{2}$"
TWITCH_DISPLAY_NAME_REGEX = r"^[a-zA-Z0-9_]{1,25}$"
TWITCH_LOGIN_NAME_REGEX = r"^[a-z0-9_]{1,25}$"
TWITCH_TOKEN_REGEX = r"^[a-zA-Z0-9]+$"
