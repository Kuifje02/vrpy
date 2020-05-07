import logging


def setup_logger():
    """Setups logger."""
    logger = logging.getLogger()

    # Logger level : DEBUG or INFO
    logger.setLevel(logging.INFO)

    # Add formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    # Show messages on terminal
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
