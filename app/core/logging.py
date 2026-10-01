from __future__ import annotations

import logging
import re
import sys

from app.core.config import APP_LOG_FILE, APP_LOG_LEVEL


LOGGER_NAME = "drucker"


class ConsoleFormatter(logging.Formatter):
    """Color only the level token in console output."""

    _LEVEL_COLORS = {
        logging.DEBUG: "\033[96m",     # cyan
        logging.INFO: "\033[92m",      # green
        logging.WARNING: "\033[93m",   # yellow
        logging.ERROR: "\033[91m",     # red
        logging.CRITICAL: "\033[95m",  # magenta
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        color = self._LEVEL_COLORS.get(record.levelno)
        if color is None:
            return formatted
        return re.sub(
            rf"(?<= ){re.escape(record.levelname)}(?= )",
            f"{color}{record.levelname}{self._RESET}",
            formatted,
            count=1,
        )


def configure_logging() -> None:
    """Configure application logging once for Streamlit and CLI execution."""
    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_drucker_configured", False):
        return

    level = getattr(logging, APP_LOG_LEVEL, logging.INFO)
    APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(
        ConsoleFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    logger._drucker_configured = True


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{component}")
