import logging
import sys
from pathlib import Path
from .config import settings

# Create logs directory if it doesn't exist
LOGS_DIR = settings.BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging():
    """
    Configure logging for the application.
    Logs will be written to both console and file.
    """
    logger = logging.getLogger("ai_audiobook_studio")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logging()
