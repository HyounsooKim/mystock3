"""
Structured logging utility for MyStock application.
Provides JSON-formatted logs for Azure Log Analytics integration.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from ..config import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """
    Configure application logging with JSON format.
    
    Returns:
        Configured logger instance
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(JSONFormatter())
    
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        **context: Additional context key-value pairs
    """
    log_func = getattr(logger, level.lower())
    extra = {"extra_fields": context}
    log_func(message, extra=extra)


# Initialize logging on module import
setup_logging()
