from __future__ import annotations

import sys
from typing import Any

from loguru import logger

_DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
    "| <level>{level: <8}</level> "
    "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "- <level>{message}</level>"
)


def configure_logging(level: str = "INFO") -> None:
    """Configure Loguru with sane defaults for CLI execution."""

    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=_DEFAULT_FORMAT,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )


def get_logger(**context: Any) -> "logger.__class__":
    """Return a contextualized logger child."""

    return logger.bind(**context)


__all__ = ["configure_logging", "get_logger", "logger"]
