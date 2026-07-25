from flask import Flask

from app.config.database import configure_database
from app.database.db import db
from app.database.seed import seed_database

from app.models.user import User
from app.models.product import Product

from app.routes.main import main
from app.routes.auth import auth
from app.routes.products import products


def create_app():

    app = Flask(__name__)

    configure_database(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(products)

    with app.app_context():
        db.create_all()
        seed_database()

    return app