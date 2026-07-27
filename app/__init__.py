import atexit
import time
import uuid

from flask import Flask, jsonify, request, g

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

from app.utils.jwt_handler import verify_token
from app.utils.logger import log_event


def create_app():

    app = Flask(__name__)

    configure_logging()
    configure_database(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(products)
    app.register_blueprint(orders)

    @app.before_request
    def log_request():

        g.request_id = str(uuid.uuid4())
        g.start_time = time.perf_counter()
        g.username = "Anonymous"

        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):

            token = auth_header.split(" ")[1]

            payload = verify_token(token)

            if payload:
                g.username = payload["username"]

        log_event(
            "HTTP_REQUEST",
            request_id=g.request_id,
            username=g.username,
            method=request.method,
            endpoint=request.path,
            ip=request.remote_addr
        )

    @app.after_request
    def log_response(response):

        response_time = round(
            (time.perf_counter() - g.start_time) * 1000,
            2
        )

        log_event(
            "HTTP_RESPONSE",
            request_id=g.request_id,
            username=g.username,
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
            response_time_ms=response_time
        )

        return response

    @app.errorhandler(Exception)
    def handle_exception(error):

        log_event(
            "APPLICATION_ERROR",
            request_id=getattr(g, "request_id", None),
            username=getattr(g, "username", "Anonymous"),
            error=str(error),
            endpoint=request.path,
            method=request.method
        )

        return jsonify(
            {
                "success": False,
                "message": "An internal server error occurred."
            }
        ), 500

    with app.app_context():
        db.create_all()
        seed_database()

    return app


app = create_app()


@atexit.register
def shutdown():
    log_event("APPLICATION_STOPPED")