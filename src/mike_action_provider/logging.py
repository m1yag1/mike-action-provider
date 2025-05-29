"""Logging configuration for the action provider."""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_config


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            str: JSON formatted log record.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        elif hasattr(record, "__dict__"):
            # Handle extra fields passed directly in __dict__
            standard_fields = {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }
            for key, value in record.__dict__.items():
                if key not in standard_fields:
                    log_data[key] = value

        # Add exception info if it exists
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Set up logging configuration.

    Args:
        log_level: The logging level to use (defaults to config value)
        log_file: Path to log file (defaults to config value)
    """
    config = get_config()
    level = log_level or config.LOG_LEVEL
    log_file = log_file or config.LOG_FILE

    # Create logs directory if it doesn't exist and file logging is enabled
    if log_file and config.ENABLE_FILE_LOGGING:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create JSON formatter
    formatter = JSONFormatter()

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if file logging is enabled and log file is specified
    if config.ENABLE_FILE_LOGGING and log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: The name for the logger, typically __name__

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
