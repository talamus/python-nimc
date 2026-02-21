"""Logging configuration"""

import sys
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any
from .settings import settings

if sys.stdout.isatty():
    COLOR = {
        "DEBUG": "\033[34m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    COLOR = {}
    BOLD = RESET = ""


class JSONFormatter(logging.Formatter):
    """JSON log formatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


class ScreenFormatter(logging.Formatter):
    """Screen friendly log formatter"""

    def format(self, record: logging.LogRecord) -> str:

        msg = f"{BOLD}{record.name:<16} {COLOR.get(record.levelname, '')}{record.levelname:>9}{RESET} {record.getMessage()}"
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return msg

    def formatException(self, exc_info: Any) -> str:
        lines = traceback.format_exception(exc_info[1], colorize=sys.stdout.isatty())
        return "".join(lines).rstrip()


# Silence noisy loggers
logging.getLogger("passlib").setLevel(logging.ERROR)
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

# Reusable config dict for both uvicorn and gunicorn
LOGGER_CONFIG = {
    "handlers": ["default"],
    "level": settings.log_level,
    "propagate": False,
}
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": JSONFormatter},
        "screen": {"()": ScreenFormatter},
        "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": settings.log_format,
        },
    },
    "root": {"handlers": ["default"], "level": settings.log_level},
    "loggers": {
        "uvicorn": LOGGER_CONFIG,
        "uvicorn.error": LOGGER_CONFIG,
        "uvicorn.access": LOGGER_CONFIG,
        "gunicorn": LOGGER_CONFIG,
        "gunicorn.error": LOGGER_CONFIG,
        "gunicorn.access": LOGGER_CONFIG,
    },
}

if settings.log_format not in LOG_CONFIG["formatters"]:
    raise ValueError(f"Invalid log format: {settings.log_format}")
