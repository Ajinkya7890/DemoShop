import logging


logger = logging.getLogger("DemoShop")


WARNING_EVENTS = {
    "USER_LOGIN_FAILED",
    "ORDER_FAILED",
    "UNAUTHORIZED_ACCESS",
}


ERROR_EVENTS = {
    "APPLICATION_ERROR",
}


def log_event(event, **kwargs):
    """
    Logs structured application events with automatic log levels.
    """

    message = event

    request_id = kwargs.pop("request_id", None)

    parts = []

    if request_id:
        parts.append(f"request_id={request_id}")

    for key, value in kwargs.items():
        parts.append(f"{key}={value}")

    if parts:
        message = f"{event} {' '.join(parts)}"

    if event in ERROR_EVENTS:
        logger.error(message)

    elif event in WARNING_EVENTS:
        logger.warning(message)

    else:
        logger.info(message)