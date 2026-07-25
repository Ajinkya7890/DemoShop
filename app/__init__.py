from flask import Flask

from app.config.database import configure_database
from app.config.logging_config import configure_logging
from app.database.db import db
from app.database.seed import seed_database

from app.models.user import User
from app.models.product import Product
from app.models.order import Order

from app.routes.main import main
from app.routes.auth import auth
from app.routes.products import products
from app.routes.orders import orders


def create_app():

    app = Flask(__name__)

    configure_logging()
    configure_database(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(products)
    app.register_blueprint(orders)

    with app.app_context():
        db.create_all()
        seed_database()

    return app