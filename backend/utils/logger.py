"""
Centralized logging configuration for all scraper modules.
Each module gets its own named logger with consistent formatting.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Create and configure a logger with both console and file handlers.

    Args:
        name: Name of the logger (typically the module name).
        log_dir: Directory for log files. Defaults to 'logs/'.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_dir)
    os.makedirs(log_path, exist_ok=True)

    # Format: [2026-04-12 10:30:00] [INFO] [upwork_scraper] Scraping started...
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler — DEBUG and above (captures everything)
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        os.path.join(log_path, f"{name}_{today}.log"), encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
