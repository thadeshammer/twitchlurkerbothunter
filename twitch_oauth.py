import os
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


class UnexpectedException(Exception):
    pass


# Disable HTTPS requirement for OAuth2 (development purposes only)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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
DOCKER_APP_URL = "http://localhost:{docker_app_port}/store_token"
PORT = 8081
REDIRECT_URI = f"http://localhost:{PORT}/callback"
AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
SCOPES = ["user:read:email", "chat:read", "chat:edit"]


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
        return f"An error occurred during login: {str(e)}"
    except UnexpectedException as e:
        return f"An unexpected error occurred during login: {str(e)}"


@app.route("/callback")
def callback():
    try:
        oauth = OAuth2Session(
            client_id, state=session["oauth_state"], redirect_uri=REDIRECT_URI
        )
        token = oauth.fetch_token(
            TOKEN_URL, authorization_response=request.url, client_secret=client_secret
        )
        session["oauth_token"] = token
        # Send the token to the Docker Flask app
        response = requests.post(
            DOCKER_APP_URL, json={"access_token": token["access_token"]}, timeout=5
        )
        if response.status_code == 200:
            return redirect(url_for(".profile"))

        return f"Failed to send token to Docker app: {response.text}"
    except MissingTokenError as e:
        return f"An error occurred during the callback: {str(e)}"
    except TokenExpiredError as e:
        return f"Token expired: {str(e)}"
    except RequestException as e:
        return f"An error occurred during the callback: {str(e)}"
    except UnexpectedException as e:
        return f"An unexpected error occurred during the callback: {str(e)}"


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
        return f"Token expired: {str(e)}"
    except RequestException as e:
        return f"An error occurred while fetching the profile: {str(e)}"
    except UnexpectedException as e:
        return f"An unexpected error occurred while fetching the profile: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
