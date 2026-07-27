from flask import Blueprint, jsonify

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


@main.route("/test-error")
def test_error():
    raise Exception("DemoShop Test Exception")