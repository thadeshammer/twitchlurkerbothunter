from flask import Blueprint, jsonify, request

from ..db import get_db
from ..models.observation import Observation
from ..models.twitch_user_data import TwitchUserData

bp = Blueprint("test_routes", __name__)


@bp.route("/")
def index():
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


@bp.route("/add_user", methods=["POST"])
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


@bp.route("/add_observation", methods=["POST"])
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
