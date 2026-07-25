import logging


logger = logging.getLogger("DemoShop")


def log_event(event, **kwargs):
    """
    Logs structured application events.

    Example:
    log_event(
        "USER_LOGIN",
        username="admin",
        status="SUCCESS"
    )
    """

    message = event

    if kwargs:
        details = " ".join(
            f"{key}={value}"
            for key, value in kwargs.items()
        )
        message = f"{event} {details}"

    logger.info(message)