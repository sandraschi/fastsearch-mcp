"""
Logging configuration for FastSearch MCP.

This module provides logging utilities following FastMCP 2.13 patterns.
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


def setup_logging(log_level: str = "INFO", format_string: str | None = None) -> None:
    """Set up logging configuration.

    Logs to stderr for Claude Desktop visibility.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger - always use stderr for Claude Desktop logs
    logging.basicConfig(level=level, format=format_string, stream=sys.stderr, force=True)


def struct_message(message: str, **kwargs) -> str:
    """Create a structured log message."""
    if kwargs:
        parts = [message]
        for key, value in kwargs.items():
            parts.append(f"{key}={value}")
        return " ".join(parts)
    return message
