import logging
import os

LOG_FOLDER = "logs"
LOG_FILE = os.path.join(LOG_FOLDER, "demoshop.log")

# Global logger that other modules can import
logger = logging.getLogger("DemoShop")


def configure_logging():

    os.makedirs(LOG_FOLDER, exist_ok=True)

    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if app reloads
    if logger.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)