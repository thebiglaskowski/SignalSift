"""Logging configuration for SignalSift."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from signalsift.config.defaults import DEFAULT_LOG_BACKUP_COUNT, DEFAULT_LOG_LEVEL, LOGS_DIR

# Global logger cache
_loggers: dict[str, logging.Logger] = {}
_initialized = False


def setup_logging(
    level: str = DEFAULT_LOG_LEVEL,
    log_file: Path | None = None,
    max_size_mb: int = 10,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
) -> None:
    """
    Set up logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to log file. If None, uses default path.
        max_size_mb: Maximum log file size in MB before rotation.
        backup_count: Number of backup files to keep.
    """
    global _initialized

    if _initialized:
        return

    # Ensure log directory exists
    if log_file is None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / "signalsift.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger("signalsift")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.
    """
    if name not in _loggers:
        if not _initialized:
            setup_logging()

        logger = logging.getLogger(
            f"signalsift.{name}" if not name.startswith("signalsift") else name
        )
        _loggers[name] = logger

    return _loggers[name]


def set_log_level(level: str) -> None:
    """Set the log level for all signalsift loggers."""
    root_logger = logging.getLogger("signalsift")
    root_logger.setLevel(getattr(logging, level.upper()))

    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(getattr(logging, level.upper()))
