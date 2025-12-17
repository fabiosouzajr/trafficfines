"""
Comprehensive logging framework for Traffic Fine Manager application.

This module provides structured logging with different log levels, error categorization,
and log rotation to prevent log files from growing too large.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with rotating file handler and console handler.
    
    Args:
        name: Logger name (typically __name__ or module name)
        log_file: Path to log file (default: 'app.log')
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB max, keep 5 backups)
    if log_file is None:
        # Default to project root if not specified
        # Calculate project root (parent of src/)
        project_root = Path(__file__).parent.parent.parent.parent
        log_file = str(project_root / 'app.log')
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.
    
    If the logger hasn't been set up yet, it will be initialized with defaults.
    Otherwise, returns the existing logger.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

