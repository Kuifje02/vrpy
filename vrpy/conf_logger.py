import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Setups logger"""
    logger = logging.getLogger()

    # DEBUG or INFO
    logger.setLevel(logging.DEBUG)

    # Add formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
