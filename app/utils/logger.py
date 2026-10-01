import json
import logging
import os
import socket
import threading
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen


logger = logging.getLogger("DemoShop")


WARNING_EVENTS = {
    "USER_LOGIN_FAILED",
    "ORDER_FAILED",
    "UNAUTHORIZED_ACCESS",
}


ERROR_EVENTS = {
    "APPLICATION_ERROR",
}


def _send_to_logsherlock(
    event,
    level,
    message,
    request_id,
    event_data,
):
    """
    Forward a structured log event to LogSherlock.

    The forwarding URL is configured through the
    LOGSHERLOCK_URL environment variable.

    Failures are intentionally ignored so that LogSherlock
    being unavailable never breaks DemoShop.
    """

    logsherlock_url = os.getenv("LOGSHERLOCK_URL")

    if not logsherlock_url:
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "DemoShop",
        "service": "DemoShop",
        "environment": os.getenv(
            "DEMOSHOP_ENVIRONMENT",
            "production"
        ),
        "host": socket.gethostname(),
        "log_level": level,
        "message": message,
        "trace_id": request_id,
        "event_id": event,
        "extra_data": event_data or None,
    }

    try:
        request = Request(
            logsherlock_url.rstrip("/") + "/logs/",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=5):
            pass

    except (URLError, TimeoutError, OSError, Exception):
        # Never allow LogSherlock connectivity problems
        # to break DemoShop.
        pass


def log_event(event, **kwargs):
    """
    Logs structured application events with automatic log levels
    and optionally forwards them to LogSherlock.
    """

    request_id = kwargs.pop("request_id", None)

    parts = []

    if request_id:
        parts.append(f"request_id={request_id}")

    for key, value in kwargs.items():
        parts.append(f"{key}={value}")

    message = event

    if parts:
        message = f"{event} {' '.join(parts)}"

    if event in ERROR_EVENTS:
        level = "ERROR"
        logger.error(message)

    elif event in WARNING_EVENTS:
        level = "WARNING"
        logger.warning(message)

    else:
        level = "INFO"
        logger.info(message)

    event_data = dict(kwargs)

    if request_id:
        event_data["request_id"] = request_id

    threading.Thread(
        target=_send_to_logsherlock,
        args=(
            event,
            level,
            message,
            request_id,
            event_data,
        ),
        daemon=True,
    ).start()