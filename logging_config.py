#!/usr/bin/env python3
"""
Centralized logging configuration for the Fortuna Bound pipeline.

Provides a single get_logger() function that:
- Reads optional LOG_LEVEL environment variable
- Writes rotating file logs to logs/pipeline.log (10 MB × 5 files)
- Echoes to console for real-time monitoring
- Ensures logs directory exists

Usage:
    from logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("This message goes to both file and console")
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

# Global logger cache to avoid duplicate setup
_loggers = {}

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with standardized configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional log level override (defaults to LOG_LEVEL env var or INFO)
        
    Returns:
        Configured logger instance
    """
    # Return cached logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Determine log level
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)
    logger.setLevel(numeric_level)
    
    # Ensure logs directory exists
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create rotating file handler (10 MB × 5 files)
    log_file = logs_dir / 'pipeline.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Apply formatter to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Cache the logger
    _loggers[name] = logger
    
    return logger


# Convenience function for backward compatibility
def setup_logging(name: str = __name__, level: str = 'INFO') -> logging.Logger:
    """
    Legacy function for backward compatibility.
    Use get_logger() for new code.
    """
    return get_logger(name, level)

