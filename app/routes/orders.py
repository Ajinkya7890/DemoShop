from flask import Blueprint, jsonify, request

from app.database.db import db
from app.models.order import Order
from app.models.product import Product
from app.utils.auth_decorator import token_required

orders = Blueprint("orders", __name__)


@orders.route("/orders", methods=["GET"])
def get_orders():

    all_orders = Order.query.order_by(Order.created_at.desc()).all()

    return jsonify(
        {
            "success": True,
            "count": len(all_orders),
            "orders": [order.to_dict() for order in all_orders]
        }
    )


@orders.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):

    order = Order.query.get(order_id)

    if order is None:
        return jsonify(
            {
                "success": False,
                "message": "Order not found."
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "order": order.to_dict()
        }
    )


@orders.route("/orders", methods=["POST"])
@token_required
def place_order(payload):

    data = request.get_json(silent=True)

    if data is None:
        return jsonify(
            {
                "success": False,
                "message": "Request body must be valid JSON."
            }
        ), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    product = Product.query.get(product_id)

    if product is None:
        return jsonify(
            {
                "success": False,
                "message": "Product not found."
            }
        ), 404

    if quantity <= 0:
        return jsonify(
            {
                "success": False,
                "message": "Quantity must be greater than 0."
            }
        ), 400

    if product.stock < quantity:
        return jsonify(
            {
                "success": False,
                "message": "Insufficient stock."
            }
        ), 400

    total_amount = product.price * quantity

    order = Order(
        username=payload["username"],
        product_id=product.id,
        quantity=quantity,
        total_amount=total_amount
    )

    product.stock -= quantity

    db.session.add(order)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Order placed successfully.",
            "order": order.to_dict()
        }
    ), 201