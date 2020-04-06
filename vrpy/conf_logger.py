import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Setups logger"""
    logger = logging.getLogger()

    # DEBUG or INFO
    logger.setLevel(logging.DEBUG)

    # Add formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    # Export messages to vrpy.log
    file_handler = RotatingFileHandler("vrpy.log", maxBytes=1000000)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # On terminal, only show INFO messages
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
