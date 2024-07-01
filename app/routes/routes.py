import logging

from flask import Flask, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.models.secrets import Secret, SecretCreate

logger = logging.getLogger(__name__)


def register_routes(app: Flask) -> None:
    @app.route("/healthcheck")
    def test():
        logger.info("/healthcheck route accessed.")
        return jsonify({"healthcheck": "achievement get"})

    # Endpoint to receive the token
    @app.route("/store-token", methods=["POST"])
    async def store_token():
        logger.info("/store-token accessed.")
        # if not request.json:
        #     logger.error("Missing JSON payload.")
        #     return jsonify({"error": "Missing JSON payload"}), 400

        # try:
        #     secret_create = SecretCreate(**request.json)
        # except ValidationError as e:
        #     logger.error(f"Validation error: {e.errors()}")
        #     return jsonify({"error": "Validation error", "details": e.errors()}), 400

        # access_token = secret_create.access_token
        # refresh_token = secret_create.refresh_token
        # expires_in = secret_create.expires_in
        # token_type = secret_create.token_type
        # scope = secret_create.scope

        # if isinstance(scope, list):
        #     scope = " ".join(scope)

        # logger.info(f"Tokens received. {expires_in=}, {token_type=}, {scope=}")

        # async with get_db() as db:
        #     try:
        #         new_secret = Secret(
        #             access_token=access_token,
        #             refresh_token=refresh_token,
        #             expires_in=expires_in,
        #             token_type=token_type,
        #             scope=scope,
        #         )
        #         db.add(new_secret)
        #         await db.commit()
        #         existing_secret = new_secret
        #     except IntegrityError:
        #         await db.rollback()
        #         # Querying the database asynchronously
        #         result = await db.execute(
        #             db.query(Secret).filter_by(enforce_one_row="enforce_one_row")
        #         )
        #         existing_secret = result.scalar()
        #         if existing_secret:
        #             existing_secret.access_token = access_token
        #             existing_secret.refresh_token = refresh_token
        #             existing_secret.expires_in = expires_in
        #             existing_secret.token_type = token_type
        #             existing_secret.scope = scope
        #             await db.commit()

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
    async def index():
        logger.info("/ route accessed.")
        async with get_db() as db:
            return jsonify({"message": "ok"})
