from app.database.db import db


def configure_database(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///demoshop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)