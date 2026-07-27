from functools import wraps

from flask import request, jsonify, g

from app.utils.jwt_handler import verify_token
from app.utils.logger import log_event


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header:

            log_event(
                "UNAUTHORIZED_ACCESS",
                request_id=getattr(g, "request_id", None),
                reason="MISSING_TOKEN",
                endpoint=request.path,
                method=request.method,
                ip=request.remote_addr
            )

            return jsonify(
                {
                    "success": False,
                    "message": "Authorization header missing."
                }
            ), 401

        if not auth_header.startswith("Bearer "):

            log_event(
                "UNAUTHORIZED_ACCESS",
                request_id=getattr(g, "request_id", None),
                reason="INVALID_AUTH_FORMAT",
                endpoint=request.path,
                method=request.method,
                ip=request.remote_addr
            )

            return jsonify(
                {
                    "success": False,
                    "message": "Invalid authorization format."
                }
            ), 401

        token = auth_header.split(" ")[1]

        payload = verify_token(token)

        if payload is None:

            log_event(
                "UNAUTHORIZED_ACCESS",
                request_id=getattr(g, "request_id", None),
                reason="INVALID_OR_EXPIRED_TOKEN",
                endpoint=request.path,
                method=request.method,
                ip=request.remote_addr
            )

            return jsonify(
                {
                    "success": False,
                    "message": "Invalid or expired token."
                }
            ), 401

        return f(payload, *args, **kwargs)

    return decorated