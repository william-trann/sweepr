"""Logging helpers for sweepr."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(verbose: bool = False, log_file: Path | None = None) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("sweepr")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stream_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(file_handler)

    return logger
