from flask import Blueprint, jsonify, request, g

from app.models.user import User
from app.utils.security import verify_password
from app.utils.jwt_handler import generate_token
from app.utils.auth_decorator import token_required
from app.utils.logger import log_event

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

        log_event(
            "USER_LOGIN_FAILED",
            request_id=g.request_id,
            username=username,
            reason="USER_NOT_FOUND",
            ip=request.remote_addr
        )

        return jsonify(
            {
                "success": False,
                "message": "User not found."
            }
        ), 404

    if not verify_password(user.password, password):

        log_event(
            "USER_LOGIN_FAILED",
            request_id=g.request_id,
            username=username,
            reason="INVALID_PASSWORD",
            ip=request.remote_addr
        )

        return jsonify(
            {
                "success": False,
                "message": "Invalid password."
            }
        ), 401

    token = generate_token(user)

    log_event(
        "USER_LOGIN_SUCCESS",
        request_id=g.request_id,
        username=user.username,
        role=user.role,
        ip=request.remote_addr
    )

    return jsonify(
        {
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": {
                "username": user.username,
                "role": user.role
            }
        }
    )


@auth.route("/profile", methods=["GET"])
@token_required
def profile(payload):
    return jsonify(
        {
            "success": True,
            "user": {
                "username": payload["username"],
                "role": payload["role"]
            }
        }
    )