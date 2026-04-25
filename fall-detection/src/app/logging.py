from __future__ import annotations

import os
import sys

from loguru import logger

_LOGGING_CONFIGURED = False


def _default_log_level() -> str:
    environment = (
        os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("PYTHON_ENV")
        or "development"
    ).strip().lower()
    if environment in {"prod", "production"}:
        return "INFO"
    return "DEBUG"


def configure_logging() -> None:
    global _LOGGING_CONFIGURED  # pylint: disable=global-statement
    if _LOGGING_CONFIGURED:
        return

    level = (os.getenv("LOG_LEVEL") or _default_log_level()).upper()
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
            "{extra[component]} | {message}"
        ),
    )

    log_file_path = (os.getenv("LOG_FILE_PATH") or "").strip()
    if log_file_path:
        logger.add(
            log_file_path,
            level=level,
            rotation="10 MB",
            retention="7 days",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
                "{extra[component]} | {message}"
            ),
        )

    _LOGGING_CONFIGURED = True


def get_logger(component: str):
    return logger.bind(component=component)
