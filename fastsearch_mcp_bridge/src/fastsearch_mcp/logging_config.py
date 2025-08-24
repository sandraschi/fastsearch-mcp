"""
Logging configuration for FastSearch MCP Bridge.

This module provides a centralized logging configuration for the FastSearch MCP Bridge,
including file and console handlers, log rotation, and structured logging.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Union

# Default log format
DEFAULT_LOG_FORMAT = (
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ' [%(filename)s:%(lineno)d] [%(process)d:%(threadName)s]'
)

# Default date format
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Default log file settings
DEFAULT_LOG_FILE = 'fastsearch_mcp.log'
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

class StructuredMessage:
    """Structured log message formatter."""
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.kwargs = kwargs
    
    def __str__(self) -> str:
        if not self.kwargs:
            return self.message
        items = ", ".join(f"{k}={v!r}" for k, v in self.kwargs.items())
        return f"{self.message} | {items}"

# Alias for easier use
struct_message = StructuredMessage

class ColorFormatter(logging.Formatter):
    """Color formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[31;1m', # Bright Red
        'RESET': '\033[0m',      # Reset
    }
    
    def format(self, record):
        """Format the specified record as text with color."""
        # Get the original format
        msg = super().format(record)
        
        # Add color if this is a console handler
        if record.levelname in self.COLORS and hasattr(record, 'colored') and record.colored:
            return f"{self.COLORS[record.levelname]}{msg}{self.COLORS['RESET']}"
        return msg

def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, file logging is disabled.
        console: Whether to enable console logging.
        max_bytes: Maximum log file size before rotation.
        backup_count: Number of backup log files to keep.
        log_format: Log message format.
        date_format: Date format for log messages.
        
    Returns:
        Root logger instance.
    """
    # Get the root logger
    logger = logging.getLogger('fastsearch_mcp')
    logger.setLevel(LOG_LEVELS.get(log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(log_format, datefmt=date_format)
    color_formatter = ColorFormatter(log_format, datefmt=date_format)
    
    # Add console handler if enabled
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(color_formatter)
        
        # Add a custom attribute to indicate this is a colored handler
        def filter_colored(record):
            record.colored = True
            return True
            
        console_handler.addFilter(filter_colored)
        logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        log_file = Path(log_file).absolute()
        
        # Create log directory if it doesn't exist
        log_dir = log_file.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler for log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Capture warnings from the warnings module
    logging.captureWarnings(True)
    
    # Set asyncio logger level
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Set log level for other loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        Configured logger instance.
    """
    if name is None:
        return logging.getLogger('fastsearch_mcp')
    return logging.getLogger(f'fastsearch_mcp.{name}')

def log_system_info(logger: logging.Logger) -> None:
    """Log system information."""
    import platform
    import psutil
    
    try:
        # System information
        system_info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'total_memory_gb': round(psutil.virtual_memory().total / (1024 ** 3), 1),
            'available_memory_gb': round(psutil.virtual_memory().available / (1024 ** 3), 1),
            'disk_usage': {}
        }
        
        # Disk usage
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                system_info['disk_usage'][part.mountpoint] = {
                    'total_gb': round(usage.total / (1024 ** 3), 1),
                    'used_gb': round(usage.used / (1024 ** 3), 1),
                    'free_gb': round(usage.free / (1024 ** 3), 1),
                    'percent_used': usage.percent
                }
            except Exception as e:
                logger.warning("Failed to get disk usage for %s: %s", part.mountpoint, e)
        
        logger.info("System information: %s", struct_message("", **system_info))
    except Exception as e:
        logger.error("Failed to log system information: %s", e, exc_info=True)

# Initialize logging when the module is imported
logger = get_logger(__name__)
