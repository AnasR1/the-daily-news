import logging
import os

LOGGING_ENABLED = os.getenv("ENABLE_LOGGING", "false").lower() == "true"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if LOGGING_ENABLED and not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    if not LOGGING_ENABLED:
        logger.addHandler(logging.NullHandler())
    
    return logger
