from flask import Blueprint, jsonify

from app.config.logging_config import logger

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def home():

    logger.info("Home endpoint accessed.")

    return jsonify(
        {
            "application": "DemoShop",
            "status": "Running"
        }
    )


@main.route("/health", methods=["GET"])
def health():

    logger.info("Health endpoint accessed.")

    return jsonify(
        {
            "status": "UP",
            "application": "DemoShop"
        }
    )