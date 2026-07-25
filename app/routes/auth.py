from flask import Blueprint, jsonify, request

from app.models.user import User
from app.utils.security import verify_password
from app.config.logging_config import logger

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET"])
def login_info():
    return jsonify(
        {
            "message": "Login endpoint is ready. Use POST to log in."
        }
    )


@auth.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if data is None:
        return jsonify(
            {
                "error": "Request body must be valid JSON."
            }
        ), 400

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user is None:
        logger.warning(f"Login failed: Unknown username '{username}'")

        return jsonify(
            {
                "success": False,
                "message": "User not found."
            }
        ), 404

    if not verify_password(user.password, password):
        logger.warning(f"Login failed: Invalid password for '{username}'")

        return jsonify(
            {
                "success": False,
                "message": "Invalid password."
            }
        ), 401

    logger.info(f"User '{username}' logged in successfully.")

    return jsonify(
        {
            "success": True,
            "message": "Login successful.",
            "username": user.username,
            "role": user.role
        }
    )