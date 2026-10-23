"""
Logging Configuration Module

Sets up logging for the entire application with rotating file handler.
Provides consistent logging across all modules.

Author: MEKKAOUI Brahim
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from src.config import get_config


class LoggerSetup:
    """Configure application-wide logging with consistent formatting."""

    _loggers = {}
    _configured = False

    @classmethod
    def setup(cls, name: str = "tourism_dashboard") -> None:
        """
        Configure root logger and apply settings from config.

        Args:
            name: Logger name (default: tourism_dashboard)
        """
        if cls._configured:
            return

        try:
            config = get_config()
            log_level = config.get('logging.level', 'INFO')
            log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            log_file = config.get('logging.file', 'logs/tourism_dashboard.log')
            max_bytes = config.get('logging.max_bytes', 10485760)
            backup_count = config.get('logging.backup_count', 5)
        except Exception:
            # Fallback to defaults if config not available
            log_level = 'INFO'
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            log_file = 'logs/tourism_dashboard.log'
            max_bytes = 10485760
            backup_count = 5

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))

        # Remove existing handlers to prevent duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(log_format)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        cls._configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger for a module.

    Ensures logging is set up and returns a configured logger.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> from src.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    # Ensure logging is configured
    LoggerSetup.setup()

    logger = logging.getLogger(name)

    # Cache logger
    LoggerSetup._loggers[name] = logger

    return logger


def set_log_level(level: str) -> None:
    """
    Set logging level for all loggers.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    for logger in LoggerSetup._loggers.values():
        logger.setLevel(getattr(logging, level.upper()))
