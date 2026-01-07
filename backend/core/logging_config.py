"""
Centralized logging configuration for the LN-Auto application.

Provides two separate log files:
1. Main application log (main.log) - For core application events
2. Plugin log (plugins.log) - For all plugin-related events
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Avoid circular import by computing LOG_DIR directly
BACKEND_DIR = Path(__file__).parent.parent
MOUNT_DIR = BACKEND_DIR / "config"
LOG_DIR = MOUNT_DIR / "logs"


# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels
DEFAULT_LOG_LEVEL = logging.INFO
DEBUG_LOG_LEVEL = logging.DEBUG

# Log file names
MAIN_LOG_FILE = "main.log"
PLUGIN_LOG_FILE = "plugins.log"

# Max log file size (10MB) and backup count
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    enable_console: bool = True,
    log_dir: Optional[Path] = None
) -> None:
    """
    Set up logging for the entire application.
    
    Args:
        log_level: The logging level to use (default: INFO)
        enable_console: Whether to log to console/stdout (default: True)
        log_dir: Directory to store log files (default: LOG_DIR from constants)
    """
    # Use provided log_dir or default from constants
    log_directory = log_dir or LOG_DIR
    
    # Ensure log directory exists
    log_directory.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler (if enabled)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Main application file handler
    main_log_path = log_directory / MAIN_LOG_FILE
    main_file_handler = RotatingFileHandler(
        main_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    main_file_handler.setLevel(log_level)
    main_file_handler.setFormatter(formatter)
    
    # Add filter to main handler to exclude plugin logs
    main_file_handler.addFilter(lambda record: not record.name.startswith('plugins.'))
    root_logger.addHandler(main_file_handler)
    
    # Plugin file handler
    plugin_log_path = log_directory / PLUGIN_LOG_FILE
    plugin_file_handler = RotatingFileHandler(
        plugin_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    plugin_file_handler.setLevel(log_level)
    plugin_file_handler.setFormatter(formatter)
    
    # Add filter to plugin handler to only include plugin logs
    plugin_file_handler.addFilter(lambda record: record.name.startswith('plugins.'))
    root_logger.addHandler(plugin_file_handler)
    
    # Log initialization message
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    logger.info(f"Main log file: {main_log_path}")
    logger.info(f"Plugin log file: {plugin_log_path}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger (typically __name__)
    
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


def get_plugin_logger(plugin_name: str) -> logging.Logger:
    """
    Get a logger instance specifically for a plugin.
    
    Plugin loggers are automatically namespaced under 'plugins.' to ensure
    they are routed to the plugin log file.
    
    Args:
        plugin_name: The name of the plugin
    
    Returns:
        A configured logger instance that writes to the plugin log file
    """
    return logging.getLogger(f"plugins.{plugin_name}")


def set_log_level(level: int) -> None:
    """
    Change the log level for all loggers at runtime.
    
    Args:
        level: The new logging level (e.g., logging.DEBUG, logging.INFO)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    for handler in root_logger.handlers:
        handler.setLevel(level)
    
    logger = get_logger(__name__)
    logger.info(f"Log level changed to: {logging.getLevelName(level)}")


def enable_debug_logging() -> None:
    """Enable debug-level logging."""
    set_log_level(DEBUG_LOG_LEVEL)


def disable_debug_logging() -> None:
    """Disable debug-level logging (revert to INFO)."""
    set_log_level(DEFAULT_LOG_LEVEL)
