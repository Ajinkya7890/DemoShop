import atexit

from app import create_app
from app.utils.logger import log_event

app = create_app()


def log_shutdown():
    log_event(
        "APPLICATION_STOPPED",
        message="DemoShop application stopped gracefully"
    )


atexit.register(log_shutdown)


if __name__ == "__main__":

    log_event(
        "APPLICATION_STARTED",
        message="DemoShop application started successfully"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )