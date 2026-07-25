from flask import Flask

from app.database.db import db
from app.database.seed import seed_database
from app.config.logging_config import logger

from app.models.user import User

from app.routes.main import main
from app.routes.auth import auth


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demoshop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    app.register_blueprint(main)
    app.register_blueprint(auth)

    logger.info("DemoShop application started.")

    return app