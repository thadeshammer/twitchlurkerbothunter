import logging
from typing import Optional

from flask import Flask, jsonify, request

from app.db import get_db
from app.models.observation import Observation
from app.models.twitch_user_data import TwitchUserData

logger = logging.getLogger(__name__)


def register_routes(app: Flask) -> None:
    @app.route("/test")
    def test():
        logger.info("/test route accessed.")
        return jsonify({"test_endpoint": "achievement get"})

    # Endpoint to receive the token
    @app.route("/store_token", methods=["POST"])
    def store_token():
        access_token: Optional[str] = None
        refresh_token: Optional[str] = None
        if request is not None and request.json is not None:
            access_token = request.json.get("access_token")
            refresh_token = request.json.get("refresh_token")

        if access_token and refresh_token:
            # TODO Store tokens in current_app.config
            return (
                jsonify(
                    {
                        "message": "Token received",
                        "access": access_token,
                        "refresh": refresh_token,
                    }
                ),
                200,
            )

        return jsonify({"error": "Missing or bad tokens"}), 400

    @app.route("/start-sweep")
    def start_sweep():
        logger.info("/start-sweep route accessed.")
        return jsonify({"start-sweep": "Not yet implemented"})

    @app.route("/scan-channel")
    def scan_channel():
        logger.info("/scan-channel route accessed.")
        return jsonify({"scan-channel": "Not yet implemented"})

    @app.route("/")
    def index():
        logger.info("/ route accessed.")
        with get_db() as db:
            users = db.query(TwitchUserData).all()
            observations = db.query(Observation).all()
            return jsonify(
                {
                    "users": [
                        {
                            "twitch_account_id": user.twitch_account_id,
                            "viewer_name": user.viewer_name,
                            "total_channels_spotted": user.total_channels_spotted,
                            "max_concurrent_channels": user.max_concurrent_channels,
                            "is_banned_or_deleted": user.is_banned_or_deleted,
                            "aliases": user.aliases,
                        }
                        for user in users
                    ],
                    "observations": [
                        {
                            "observation_id": obs.observation_id,
                            "twitch_account_id": obs.twitch_account_id,
                            "viewer_name": obs.viewer_name,
                            "channel_id": obs.channel_id,
                            "channel_name": obs.channel_name,
                            "category": obs.category,
                            "viewer_count": obs.viewer_count,
                            "processing_time": obs.processing_time,
                            "timestamp": obs.timestamp,
                        }
                        for obs in observations
                    ],
                }
            )

    @app.route("/add_user", methods=["POST"])
    def add_user():
        with get_db() as db:
            user_data = request.json
            if user_data is not None:
                new_user = TwitchUserData(
                    twitch_account_id=user_data["twitch_account_id"],
                    viewer_name=user_data["viewer_name"],
                    total_channels_spotted=user_data["total_channels_spotted"],
                    max_concurrent_channels=user_data["max_concurrent_channels"],
                    is_banned_or_deleted=user_data["is_banned_or_deleted"],
                    aliases=user_data.get("aliases", []),
                )
                db.add(new_user)
                db.commit()
                return jsonify({"message": "User added successfully"}), 201
            else:
                return jsonify({"error": "Invalid input"}), 400

    @app.route("/add_observation", methods=["POST"])
    def add_observation():
        with get_db() as db:
            observation_data = request.json
            if observation_data is not None:
                new_observation = Observation(
                    observation_id=observation_data["observation_id"],
                    twitch_account_id=observation_data["twitch_account_id"],
                    viewer_name=observation_data["viewer_name"],
                    channel_id=observation_data["channel_id"],
                    channel_name=observation_data["channel_name"],
                    category=observation_data["category"],
                    viewer_count=observation_data["viewer_count"],
                    processing_time=observation_data["processing_time"],
                    timestamp=observation_data["timestamp"],
                )
                db.add(new_observation)
                db.commit()
                return jsonify({"message": "Observation added successfully"}), 201
            else:
                return jsonify({"error": "Invalid input"}), 400
