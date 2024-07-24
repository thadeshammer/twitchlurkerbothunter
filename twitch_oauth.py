# quick and dirty serlet to handle twitch-oauth for us
import os
import ssl
import threading
import webbrowser
from typing import List, Union

import requests
import yaml
from flask import Flask, redirect, request, session, url_for
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests.exceptions import RequestException
from requests_oauthlib import OAuth2Session
from requests_oauthlib.oauth2_session import TokenExpiredError


class TwitchOAuthServletException(Exception):
    pass


class UnexpectedException(Exception):
    pass


class MissingCredentials(Exception):
    pass


app = Flask(__name__)

# FLASK SECRET KEY
# Incase I forget what this is for again:

# Session Management: Flask uses the secret key to sign session cookies. This ensures that the
# cookies  cannot be tampered with. When Flask sets a session cookie, it signs it with the secret
# key. When a request with the session cookie is received, Flask verifies the signature using the
# secret key. If the signature is valid, Flask knows the cookie hasn’t been altered.

# CSRF Protection: If you are using Flask-WTF or another extension to protect against Cross-Site
# Request Forgery (CSRF) attacks, the secret key is used to generate tokens that prevent these
# attacks.

# Encryption: The secret key can also be used for encrypting sensitive data within your application.
with open("./secrets/secret_key.txt", "r", encoding="UTF8") as file:
    app.secret_key = file.read().strip()

# Get the Twitch client id and client secret for this registered app.
with open("./secrets/tokens.yaml", "r", encoding="UTF8") as file:
    tokens_file: Union[dict, List, None] = yaml.safe_load(file)

if not isinstance(tokens_file, dict):
    raise TypeError("Tokens file incorrectly formatted.")

CERT_PASSKEY = str(os.getenv("CERT_PASSKEY"))
client_id: str = tokens_file["TWITCH_CLIENT_ID"]
client_secret: str = tokens_file["TWITCH_CLIENT_SECRET"]

if not CERT_PASSKEY or not client_id or not client_secret:
    raise MissingCredentials("A required credential is missing.")

DOCKER_APP_PORT = 443
DOCKER_APP_URL = f"https://localhost:{DOCKER_APP_PORT}/store-token"
PORT = 8081
REDIRECT_URI = f"https://localhost:{PORT}/callback"
AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
# SCOPES = ["chat:read", "chat:edit"]
# SCOPES = ["chat:read", "user:read:chat", "user:bot"]
SCOPES = ["chat:read"]  # minimalist approach


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login")
def login():
    try:
        oauth = OAuth2Session(client_id, redirect_uri=REDIRECT_URI, scope=SCOPES)
        authorization_url, state = oauth.authorization_url(AUTHORIZE_URL)
        session["oauth_state"] = state

        # Path to Chrome executable
        chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s"
        threading.Timer(
            1.25, lambda: webbrowser.get(chrome_path).open(authorization_url)
        ).start()  # Open browser
        return redirect(authorization_url)
    except RequestException as e:
        raise TwitchOAuthServletException(
            f"An error occurred during login: {str(e)}"
        ) from e
    except UnexpectedException as e:
        raise TwitchOAuthServletException(
            f"An unexpected error occurred during login: {str(e)}"
        ) from e


@app.route("/callback")
def callback():
    try:
        # We don't need to store this instance, but instantiating it sets the session up.
        # Below we manually parse the response because the fetch_token() call for some reason
        # isn't working with Twitch's response.
        OAuth2Session(
            client_id, state=session["oauth_state"], redirect_uri=REDIRECT_URI
        )

        # Manually perform the token exchange
        token_data = {
            "grant_type": "authorization_code",
            "code": request.args.get("code"),
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        response = requests.post(TOKEN_URL, data=token_data, timeout=5)
        token_response = response.json()

        if "access_token" in token_response:
            access_token = token_response["access_token"]
            refresh_token = token_response["refresh_token"]
            print(f"DEBUG >> {access_token=}, {refresh_token=}")

            session["oauth_token"] = token_response
            # Send the tokens to the Docker Flask app
            docker_app_response = requests.post(
                DOCKER_APP_URL,
                json={
                    "access_token": token_response["access_token"],
                    "refresh_token": token_response["refresh_token"],
                    "expires_in": token_response["expires_in"],
                    "token_type": token_response["token_type"],
                    "scope": token_response["scope"],
                },
                timeout=5,
                verify=False,
            )
            if docker_app_response.status_code == 200:
                return redirect(url_for("profile"))
            return f"Failed to send token to Docker app: {docker_app_response.text}"

        return "An error occurred: Token not found in the response."

    except MissingTokenError as e:
        raise TwitchOAuthServletException(
            f"An error occurred during the callback (MissingTokenError): {str(e)}"
        ) from e
    except TokenExpiredError as e:
        raise TwitchOAuthServletException(f"Token expired: {str(e)}") from e
    except RequestException as e:
        raise TwitchOAuthServletException(
            f"An error occurred during the callback (RequestException): {str(e)}"
        ) from e
    except UnexpectedException as e:
        raise TwitchOAuthServletException(f"An unknown error occurred: {str(e)}") from e


@app.route("/profile")
def profile():
    try:
        oauth = OAuth2Session(client_id, token=session["oauth_token"])
        headers = {
            "Authorization": f"Bearer {session['oauth_token']['access_token']}",
            "Client-ID": client_id,
        }
        response = oauth.get("https://api.twitch.tv/helix/users", headers=headers)
        return response.json()
    except TokenExpiredError as e:
        raise TwitchOAuthServletException(f"Token expired: {str(e)}") from e
    except RequestException as e:
        raise TwitchOAuthServletException(
            f"An error occurred while fetching the profile: {str(e)}"
        ) from e
    except UnexpectedException as e:
        raise TwitchOAuthServletException(
            f"An unexpected error occurred while fetching the profile: {str(e)}"
        ) from e


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile="./secrets/cert.pem",
        keyfile="./secrets/key.pem",
        password=CERT_PASSKEY,
    )

    app.run(debug=True, ssl_context=context, port=PORT)
