import logging

from flask import Flask, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.models.secrets import Secret, SecretCreate

logger = logging.getLogger(__name__)


def register_routes(app: Flask) -> None:
    @app.route("/test")
    def test():
        logger.info("/test route accessed.")
        return jsonify({"test_endpoint": "achievement get"})

    # Endpoint to receive the token
    @app.route("/store_token", methods=["POST"])
    def store_token():
        if not request.json:
            return jsonify({"error": "Missing JSON payload"}), 400

        try:
            # Validate and parse the request data using Pydantic
            secret_create = SecretCreate(**request.json)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.errors()}), 400

        # Extract values from the validated Pydantic model
        access_token = secret_create.access_token
        refresh_token = secret_create.refresh_token
        expires_in = secret_create.expires_in
        token_type = secret_create.token_type
        scope = secret_create.scope

        # Handle scope if it's a list
        if isinstance(scope, list):
            scope = " ".join(scope)

        logger.info(f"Tokens received. {expires_in=}, {token_type=}, {scope=}")

        # Use get_db context manager to handle the database session
        with get_db() as db:
            try:
                # Try to insert the new row, which will fail if the unique constraint is violated
                new_secret = Secret(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                    token_type=token_type,
                    scope=scope,
                )
                db.add(new_secret)
                db.commit()
                existing_secret = new_secret
            except IntegrityError:
                db.rollback()
                # If the insertion fails, update the existing row
                existing_secret = (
                    db.query(Secret)
                    .filter_by(enforce_one_row="enforce_one_row")
                    .first()
                )
                if existing_secret:
                    existing_secret.access_token = access_token
                    existing_secret.refresh_token = refresh_token
                    existing_secret.expires_in = expires_in
                    existing_secret.token_type = token_type
                    existing_secret.scope = scope
                    db.commit()

        # Return the stored secret using Pydantic model for serialization
        return jsonify({"message": "ok"}), 200

    @app.route("/start-scan")
    def start_scan():
        logger.info("/start-scan route accessed.")
        return jsonify({"start-scan": "Not yet implemented"})

    @app.route("/fetch-channel-viewerlist")
    def fetch_channel_viewerlist():
        logger.info("/fetch-channel-viewerlist route accessed.")
        return jsonify({"fetch-channel-viewerlist": "Not yet implemented"})

    @app.route("/")
    def index():
        logger.info("/ route accessed.")
        with get_db() as db:
            return jsonify({"message": "ok"})
