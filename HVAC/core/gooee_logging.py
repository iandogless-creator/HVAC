"""
Module 65 — Logging Subsystem for HVACgooee
===========================================

Provides a unified logging interface for:
    - core hydronics
    - DXF engine
    - GUI
    - CLI

Creates/uses:
    logs/gooee.log

Supports:
    - console output
    - file logging
    - log rotation (5 files, 1MB each)
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


DEFAULT_LOG_NAME = "gooee"
DEFAULT_LOG_FILE = "logs/gooee.log"


def get_logger(name: str = DEFAULT_LOG_NAME) -> logging.Logger:
    """
    Return a configured logger.
    Safe to call from ANY module.
    Logger is configured only once (singleton style).
    """

    logger = logging.getLogger(name)

    if getattr(logger, "_gooee_configured", False):
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure logs/ directory exists
    base_dir = os.getcwd()
    log_path = os.path.join(base_dir, DEFAULT_LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # ------------------------------------------------------------
    # File handler (rotating)
    # ------------------------------------------------------------
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,  # 1MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # ------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger._gooee_configured = True
    logger.debug("Gooee logging system initialised.")
    return logger


# ----------------------------------------------------------------------
# Convenience wrappers
# ----------------------------------------------------------------------

def log_info(msg: str):
    get_logger().info(msg)


def log_warn(msg: str):
    get_logger().warning(msg)


def log_error(msg: str):
    get_logger().error(msg)


def log_debug(msg: str):
    get_logger().debug(msg)
