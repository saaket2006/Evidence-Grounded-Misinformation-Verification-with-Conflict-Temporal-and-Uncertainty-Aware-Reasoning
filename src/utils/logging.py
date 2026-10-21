"""Pipeline stage logger."""

import logging
import sys


def setup_logger(name: str = "misinfo_verification", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()


def log_stage(stage_name: str, message: str) -> None:
    """Log a specific stage in the verification pipeline."""
    logger.info(f"[{stage_name.upper()}] {message}")
