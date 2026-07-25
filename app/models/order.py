from datetime import datetime

from app.database.db import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    total_amount = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Placed"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_amount": self.total_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }