
from flask import Blueprint, jsonify

from app.utils.resource_guard import get_resource_health

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return jsonify(
        {
            "success": True,
            "message": "Welcome to DemoShop API!"
        }
    )


@main.route("/health")
def health():
    return jsonify(
        {
            "success": True,
            "status": "healthy"
        }
    )


@main.route("/resource-health", methods=["GET"])
def resource_health():
    resource_status = get_resource_health()

    return jsonify(
        {
            "success": True,
            **resource_status
        }
    )


@main.route("/test-error")
def test_error():
    raise Exception("DemoShop Test Exception")
