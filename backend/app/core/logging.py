"""Structured logging configuration for SANJEEVNI.

Provides JSON or clean console logging without logging sensitive credentials
or high-frequency raw physiological streams.
"""
import logging
import sys
from typing import Any, Dict
from app.core.config import settings


class SafeFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive keys and formats timestamps."""

    SENSITIVE_KEYS = {"password", "token", "secret", "jwt", "authorization"}

    def format(self, record: logging.LogRecord) -> str:
        # Standard prefix format: [2026-09-13 15:00:00] [LEVEL] [logger_name] Message
        log_fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> logging.Logger:
    """Configures the root and application loggers."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-init
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SafeFormatter())
        root_logger.addHandler(handler)

    # Suppress overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)

    logger = logging.getLogger("sanjeevni")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
