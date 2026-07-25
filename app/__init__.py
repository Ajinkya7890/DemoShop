from flask import Flask

from app.routes import main
from app.database.db import db
from app.config.logging_config import logger

# Import models so SQLAlchemy knows about them
from app.models.user import User


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demoshop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main)

    logger.info("DemoShop application started.")

    return app