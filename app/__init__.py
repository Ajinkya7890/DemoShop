from flask import Flask

from app.routes import main
from app.config.logging_config import logger


def create_app():
    app = Flask(__name__)

    app.register_blueprint(main)

    logger.info("DemoShop application started.")

    return app