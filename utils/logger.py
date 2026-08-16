"""
Logging utility for the automation framework.
Provides structured logging with file and console output.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "reports" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"test_run_{timestamp}.log"


def setup_logger(name: str = "ebay_automation") -> logging.Logger:
    """Configure and return a logger instance."""
    _logger = logging.getLogger(name)

    if _logger.handlers:
        return _logger

    _logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )
    file_handler.setFormatter(file_format)

    _logger.addHandler(console_handler)
    _logger.addHandler(file_handler)

    return _logger


logger = setup_logger()
