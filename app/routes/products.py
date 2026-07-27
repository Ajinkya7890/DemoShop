from flask import Blueprint, jsonify, request, g

from app.database.db import db
from app.models.product import Product
from app.utils.auth_decorator import token_required
from app.utils.logger import log_event

products = Blueprint("products", __name__)


@products.route("/products", methods=["GET"])
def get_products():

    all_products = Product.query.all()

    return jsonify(
        {
            "success": True,
            "count": len(all_products),
            "products": [product.to_dict() for product in all_products]
        }
    )


@products.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = Product.query.get(product_id)

    if product is None:
        return jsonify(
            {
                "success": False,
                "message": "Product not found."
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "product": product.to_dict()
        }
    )


@products.route("/products", methods=["POST"])
@token_required
def add_product(payload):

    data = request.get_json(silent=True)

    if data is None:
        return jsonify(
            {
                "success": False,
                "message": "Request body must be valid JSON."
            }
        ), 400

    product = Product(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price"),
        stock=data.get("stock", 0)
    )

    db.session.add(product)
    db.session.commit()

    log_event(
        "PRODUCT_CREATED",
        request_id=g.request_id,
        product_id=product.id,
        name=product.name,
        created_by=payload["username"]
    )

    return jsonify(
        {
            "success": True,
            "message": "Product added successfully.",
            "product": product.to_dict()
        }
    ), 201


@products.route("/products/<int:product_id>", methods=["PUT"])
@token_required
def update_product(payload, product_id):

    product = Product.query.get(product_id)

    if product is None:
        return jsonify(
            {
                "success": False,
                "message": "Product not found."
            }
        ), 404

    data = request.get_json(silent=True)

    if data is None:
        return jsonify(
            {
                "success": False,
                "message": "Request body must be valid JSON."
            }
        ), 400

    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price = data.get("price", product.price)
    product.stock = data.get("stock", product.stock)

    db.session.commit()

    log_event(
        "PRODUCT_UPDATED",
        request_id=g.request_id,
        product_id=product.id,
        updated_by=payload["username"]
    )

    return jsonify(
        {
            "success": True,
            "message": "Product updated successfully.",
            "product": product.to_dict()
        }
    )


@products.route("/products/<int:product_id>", methods=["DELETE"])
@token_required
def delete_product(payload, product_id):

    product = Product.query.get(product_id)

    if product is None:
        return jsonify(
            {
                "success": False,
                "message": "Product not found."
            }
        ), 404

    deleted_product_id = product.id
    deleted_product_name = product.name

    db.session.delete(product)
    db.session.commit()

    log_event(
        "PRODUCT_DELETED",
        request_id=g.request_id,
        product_id=deleted_product_id,
        name=deleted_product_name,
        deleted_by=payload["username"]
    )

    return jsonify(
        {
            "success": True,
            "message": "Product deleted successfully."
        }
    )