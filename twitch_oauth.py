# quick and dirty serlet to handle twitch-oauth for us
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


app = Flask(__name__)

# Read the Flask secret key
with open("./secrets/secret_key.txt", "r", encoding="UTF8") as file:
    app.secret_key = file.read().strip()

# Get the client id and secret
with open("./secrets/tokens.yaml", "r", encoding="UTF8") as file:
    tokens_file: Union[dict, List, None] = yaml.safe_load(file)

assert isinstance(tokens_file, dict)
client_id: str = tokens_file["TWITCH_CLIENT_ID"]
client_secret: str = tokens_file["TWITCH_CLIENT_SECRET"]

DOCKER_APP_PORT = 8000
DOCKER_APP_URL = f"http://localhost:{DOCKER_APP_PORT}/store_token"
PORT = 8081
REDIRECT_URI = f"https://localhost:{PORT}/callback"
AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
SCOPES = ["chat:read", "chat:edit"]


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
    app.run(
        debug=True, ssl_context=("./secrets/cert.pem", "./secrets/key.pem"), port=PORT
    )
