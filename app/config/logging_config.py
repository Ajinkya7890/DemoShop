import logging
import os

LOG_DIRECTORY = "logs"
LOG_FILE = os.path.join(LOG_DIRECTORY, "application.log")

os.makedirs(LOG_DIRECTORY, exist_ok=True)

logger = logging.getLogger("DemoShop")

logger.setLevel(logging.INFO)

if not logger.handlers:

    file_handler = logging.FileHandler(LOG_FILE)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)