"""Logging utility for the weed removal system."""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class Logger:
    """Configure and manage application logging."""

    def __init__(self):
        """Initialize logger."""
        self._configured = False

    def setup(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,
        backup_count: int = 5
    ):
        """
        Setup logging configuration.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        if self._configured:
            return

        # Remove default handler
        logger.remove()

        # Add console handler with colors
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True
        )

        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=log_level,
                rotation=max_bytes,
                retention=backup_count,
                compression="zip"
            )

        self._configured = True
        logger.info(f"Logging configured with level: {log_level}")

    def get_logger(self, name: str = None):
        """
        Get logger instance.

        Args:
            name: Logger name (usually module name)

        Returns:
            Logger instance
        """
        if not self._configured:
            self.setup()

        if name:
            return logger.bind(name=name)
        return logger


# Global logger instance
app_logger = Logger()
