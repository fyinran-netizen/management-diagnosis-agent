from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from app.core.config import PROJECT_ROOT


LOGGER_NAME = "drucker"
DEFAULT_LOG_FILE = PROJECT_ROOT / ".runtime" / "logs" / "application.log"


def configure_logging() -> None:
    """Configure application logging once for Streamlit and CLI execution."""
    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_drucker_configured", False):
        return

    level_name = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = Path(os.getenv("APP_LOG_FILE", str(DEFAULT_LOG_FILE)))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    logger._drucker_configured = True


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{component}")
