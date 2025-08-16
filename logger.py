"""
Simple logging setup. No fancy structured logging yet - just basic improvements.
"""
import logging
from config import settings

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_logger(name: str):
    """Get a logger for a specific module."""
    return logging.getLogger(name)

# Initialize logging
setup_logging()