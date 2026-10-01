from app.database.db import db
from app.models.user import User
from app.utils.security import hash_password


def seed_database():
    """
    Seed the database with a default admin user.
    """

    admin = User.query.filter_by(username="admin").first()

    if admin is None:
        admin = User(
            username="admin",
            password=hash_password("admin123"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("✅ Default admin user created.")
    else:
        print("ℹ️ Admin user already exists.")