"""Logger configuration module."""
import logging
from pathlib import Path
from src.config import settings


def setup_logger():
    """Setup logger with console and file handlers."""
    # Create logs directory
    Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("usp_music_finder")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.FileHandler(
        f"{settings.LOGS_DIR}/bot.log",
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
